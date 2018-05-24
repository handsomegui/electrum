from . import utils
from . import gui
from . import txdetail
from . import addresses
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
from .uikit_bindings import *
from .custom_objc import *
from collections import namedtuple

CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change base_unit")

CellIdentifiers = ( "CoinsCell", "EmptyCell")

class CoinsTableVC(UITableViewController):
    ''' Coins Tab -- shows utxos
    '''
    needsRefresh = objc_property()
    blockRefresh = objc_property()
    selected = objc_property() # NSArray of entry.name strings
    clearBut = objc_property()
    spendBut = objc_property()

    @objc_method
    def initWithStyle_(self, style : int) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
        self.blockRefresh = False
        self.title = _("Coins")
        self.selected = []
        self.tabBarItem.image = UIImage.imageNamed_("tab_coins_new")
      
        buts = [
            UIBarButtonItem.alloc().initWithTitle_style_target_action_(_("Spend"), UIBarButtonItemStyleDone, self, SEL(b'spendFromSelection')).autorelease(),
            UIBarButtonItem.alloc().initWithTitle_style_target_action_(_("Clear"), UIBarButtonItemStylePlain, self, SEL(b'clearSelection')).autorelease(),
        ]
        self.spendBut = buts[0]
        self.clearBut = buts[1]
        self.spendBut.enabled = False
        self.clearBut.enabled = False
        self.navigationItem.rightBarButtonItems = buts
        
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()

        gui.ElectrumGui.gui.sigCoins.connect(lambda: self.refresh(), self)

        return self

    @objc_method
    def dealloc(self) -> None:
        gui.ElectrumGui.gui.sigCoins.disconnect(self)
        self.needsRefresh = None
        self.blockRefresh = None
        self.selected = None
        self.clearBut = None
        self.spendBut = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        nib = UINib.nibWithNibName_bundle_(CellIdentifiers[0], None)
        self.tableView.registerNib_forCellReuseIdentifier_(nib, CellIdentifiers[0])
        self.refresh()
        
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        try:
            coins = _Get(self)
            return len(coins) if coins else 1
        except:
            print("Error, exception retrieving coins from nspy cache")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        try:
            coins = _Get(self)
            identifier = CellIdentifiers[0 if coins else -1]
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            parent = gui.ElectrumGui.gui
            isGood = True
            if cell is None:
                cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
                isGood = False
            if coins and isGood:
                entry = coins[indexPath.row]
                idx = indexPath.row
                setup_cell_for_coins_entry(cell, entry)
                cell.tag = idx
                def linkTapped(acell : ObjCInstance) -> None:
                    self.onOptions_(cell)
                def butTapped(acell : ObjCInstance) -> None:
                    self.selectDeselectCell_(cell)
                def doDetail(acell : ObjCInstance) -> None:
                    # TODO: detail view push here
                    gui.ElectrumGui.gui.show_error('Coins Detail Screen Coming soon!', 'Unimplemented')
                cell.onAddress = Block(linkTapped)
                cell.onButton = Block(butTapped)
                cell.onAccessory = Block(doDetail)
                self.setupSelectionButtonCell_atIndex_(cell, idx)
                    
            else:
                empty_cell(cell,_("No coins"),True)
        except Exception as e:
            utils.NSLog("exception in Coins tableView_cellForRowAtIndexPath_: %s",str(e))
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, CellIdentifiers[-1]).autorelease()
            empty_cell(cell)
        return cell
    
    
    @objc_method
    def showTxDetailForIndex_(self, index : int) -> None:
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = _Get(self)[index]
            hentry = parent.get_history_entry(entry.tx_hash)
            if hentry is None: raise Exception("NoHEntry")
        except:
            import sys
            utils.NSLog("CoinsTableVC.showTxDetailForIndex got exception: %s",str(sys.exc_info()[1]))
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        rawtx = None
        if tx is None:
            raise Exception("Could not find Transaction for tx '%s'"%str(entry.tx_hash))
        self.navigationController.pushViewController_animated_(txdetail.CreateTxDetailWithEntry(hentry, tx=tx), True)
    
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR ROW %d"%indexPath.row)
        animated = True

        cell = tv.cellForRowAtIndexPath_(indexPath)
        if cell:
            animated = self.selectDeselectCell_(cell)

        tv.deselectRowAtIndexPath_animated_(indexPath, animated)
        
    @objc_method
    def selectDeselectCell_(self, cell : ObjCInstance) -> bool: # returns False IFF it was a frozen address and select/deselect failed
        coins = _Get(self)
        if not coins or not len(coins): return True

        index = cell.tag
        self.setIndex_selected_(index, not self.isIndexSelected_(index))
        wasSel = self.setupSelectionButtonCell_atIndex_(cell, index) # this sometimes fails if address is frozen and/or we are watching only
        self.setIndex_selected_(index, wasSel)

        self.selected = self.updateSelectionButtons()
        
        # animate to indicate to user why they were DENIED
        if not wasSel and index < len(coins) and coins[index].is_frozen:
            cell.amount.textColorAnimationFromColor_toColor_duration_reverses_completion_(
                utils.uicolor_custom('frozentext'),
                utils.uicolor_custom('frozentextbright'),
                0.4, True, None
            )
            cell.flags.textColorAnimationFromColor_toColor_duration_reverses_completion_(
                utils.uicolor_custom('frozentext'),
                utils.uicolor_custom('frozentextbright'),
                0.4, True, None
            )
            return False
        return True
        
 
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        coins = _Get(self)
        if coins and indexPath.row < len(coins):
            # NEW layout: 113 for no desc, 136 for desc
            lbl = coins[indexPath.row].label
            return 136.0 if lbl and lbl.strip() else 113.0
        return 44.0
   
    @objc_method
    def refresh(self):
        self.needsRefresh = True # mark that a refresh was called in case refresh is blocked
        if self.blockRefresh:
            return
        if self.refreshControl: self.refreshControl.endRefreshing()
        self.selected = self.updateSelectionButtons()
        if self.tableView:
            self.tableView.reloadData()
        self.needsRefresh = False


    @objc_method
    def doRefreshIfNeeded(self):
        if self.needsRefresh:
            self.refresh()
            #print ("COINS REFRESHED")

            
    @objc_method
    def onOptions_(self, obj : ObjCInstance) -> None:
        #print ("On Options But")
        try:
            if isinstance(obj, UIGestureRecognizer):
                obj = obj.view
            elif isinstance(obj, UITableViewCell):
                pass
            entry = _Get(self)[obj.tag]
            parent = gui.ElectrumGui.gui
            def on_block_explorer() -> None:
                parent.view_on_block_explorer(entry.tx_hash, 'tx')
            def on_request_payment() -> None:
                parent.jump_to_receive_with_address(entry.address)
            def on_address_details() -> None:                
                addrDetail = addresses.PushDetail(entry.address, self.navigationController)
            def spend_from2(utxos : list) -> None:
                validSels = list(self.updateSelectionButtons())
                coins = _Get(self)
                for entry in coins:
                    if entry.name in validSels and entry.utxo not in utxos:
                        utxos.append(entry.utxo)
                if utxos:
                    spend_from(utxos)
    
            actions = [
                    [ _('Copy Address'), parent.copy_to_clipboard, entry.address_str, _('Address') ],
                    [ _('Copy UTXO'), parent.copy_to_clipboard, entry.name, _('UTXO') ],
                    [ _('Cancel') ],
                    [ _("Address Details"), on_address_details ],
                    [ _("Transaction Details"), lambda: self.showTxDetailForIndex_(obj.tag)],
                    [ _("Request payment"), on_request_payment ],
                ]
            
            watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True
    
            if not watch_only:
                actions.append([ _('Freeze') if not entry.is_frozen else _('Unfreeze'), lambda: toggle_freeze(entry) ])
    
            if not watch_only and not entry.is_frozen:
                actions.append([ _('Spend from this UTXO'), lambda: spend_from([entry.utxo]) ] )
                if len(list(self.updateSelectionButtons())):
                    actions.append([ _('Spend from this UTXO + Selected'), lambda: spend_from2([entry.utxo]) ] )

            # make sure this is last
            actions.append([ _("View on block explorer"), on_block_explorer ] )           
                    
            utils.show_alert(
                vc = self,
                title = _("Options"),
                message = _("Output") + ":" + " " + entry.name[0:10] + "..." + entry.name[-2:],
                actions = actions,
                cancel = _('Cancel'),
                style = UIAlertControllerStyleActionSheet,
                ipadAnchor =  obj.convertRect_toView_(obj.bounds, self.view)
            )
            #print ("address =", entry.address_str)
        except:
            import sys
            utils.NSLog("Exception during coins.py 'onOptions': %s",str(sys.exc_info()[1]))

    @objc_method
    def isIndexSelected_(self, index : int) -> bool:
        try:
            entry = _Get(self)[index]
            sels = set(list(self.selected))
            return bool(entry.name in sels)
        except:
            import sys
            utils.NSLog("Exception during coins.py 'isIndexSelected': %s",str(sys.exc_info()[1]))
        return False

    @objc_method
    def setIndex_selected_(self, index : int, b : bool) -> None:
        try:
            entry = _Get(self)[index]
            sels = set(list(self.selected))
            if not b: sels.discard(entry.name)
            else: sels.add(entry.name)
            self.selected = list(sels)
        except:
            import sys
            utils.NSLog("Exception during coins.py 'setIndex_selected_': %s",str(sys.exc_info()[1]))

    @objc_method
    def clearSelection(self) -> None:
        self.selected = []
        self.refresh()
        
    @objc_method
    def spendFromSelection(self) -> None:
        #print ("spend selected...")
        validSels = list(self.updateSelectionButtons())
        #print("valid selections:",*validSels)
        coins = _Get(self)
        utxos = []
        for entry in coins:
            if entry.name in validSels:
                utxos.append(entry.utxo)
        if utxos:
            spend_from(utxos)
        
    @objc_method
    def updateSelectionButtons(self) -> ObjCInstance:
        parent = gui.ElectrumGui.gui
        newSels = set()
        self.clearBut.enabled = False
        self.spendBut.enabled = False
        if parent.wallet and not parent.wallet.is_watching_only():
            sels = set(list(self.selected))
            coins = _Get(self)
            for coin in coins:
                if not coin.is_frozen and coin.name in sels:
                    newSels.add(coin.name)
            if len(newSels):
                self.spendBut.enabled = True
            if len(sels):
                self.clearBut.enabled = True
        return ns_from_py(list(newSels))
    
    @objc_method
    def setupSelectionButtonCell_atIndex_(self, cell, index : int) -> bool:
        if not isinstance(cell, CoinsCell):
            utils.NSLog("*** WARNING: setupSelectionButtonCell_atIndex_ called with an unknown cell type! Returning early...")
            return False
        parent = gui.ElectrumGui.gui
        no_good = parent.wallet is None or parent.wallet.is_watching_only()
        try:
            entry = _Get(self)[index]
            if entry.is_frozen:
                no_good = True
        except:
            no_good = True
        
        ret = False
        
        if no_good or not self.isIndexSelected_(index):
            cell.buttonSelected = False
        else:
            cell.buttonSelected = True
            ret = True
            
        cell.buttonEnabled = not no_good
        
        return ret


def setup_cell_for_coins_entry(cell : ObjCInstance, entry : CoinsEntry) -> None:
    if not isinstance(cell, CoinsCell):
        empty_cell(cell)
        return

    #CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change base_unit")


    cell.onAddress = None # clear objc blocks.. caller sets these
    cell.onButton = None
    # initialize it to base values
    cell.buttonSelected = False
    cell.chevronHidden = False
    
    
    cell.address.attributedText = NSAttributedString.alloc().initWithString_attributes_(
        entry.address_str,
        {
            NSUnderlineStyleAttributeName : NSUnderlineStyleSingle
        }    
    ).autorelease()
    
    kern = utils._kern
    
    cell.amountTit.setText_withKerning_(_("Amount"), kern)
    cell.utxoTit.setText_withKerning_(_("UTXO"), kern)
    cell.heightTit.setText_withKerning_(_("Height"), kern)

    cell.desc.setText_withKerning_(entry.label.strip() if entry.label else '', kern)

    cell.utxo.setText_withKerning_(str(entry.name), kern)
    specialColor = utils.uicolor_custom('dark')
    if entry.is_frozen:
        cell.flags.text = _("Frozen")
        specialColor = utils.uicolor_custom('frozentext')
    else:
        cell.flags.text = _("Change") if entry.is_change else _("Receiving")
    cell.amount.text = entry.amount_str + ' ' + entry.base_unit
    cell.height.text = str(entry.height)

    cell.amount.textColor = specialColor
    cell.flags.textColor = specialColor


def _Get(coinsvc : CoinsTableVC) -> list:
    return gui.ElectrumGui.gui.sigCoins.get(utils.nspy_get_byname(coinsvc, 'domain'))

from typing import Any
class CoinsMgr(utils.DataMgr):
    def doReloadForKey(self, key : Any) -> Any:
        t0 = time.time()    
        c = get_coins(key)
        utils.NSLog("CoinsMgr: Fetched %d utxo entries [domain=%s] in %f ms", len(c), str(key)[:16], (time.time()-t0)*1e3)
        return c

def get_coin_counts(domain : list, exclude_frozen : bool = False, mature : bool = False, confirmed_only : bool = False) -> int:
    ''' Like the below but just returns the counts.. a slight optimization for addresses.py which just cares about counts. '''
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    if wallet is None:
        utils.NSLog("get_coin_counts: wallet was None, returning early")
        return 0
    c = wallet.get_utxos(domain, exclude_frozen, mature, confirmed_only)
    return len(c) if c else 0

def get_coins(domain : list = None, exclude_frozen : bool = False, mature : bool = False, confirmed_only : bool = False) -> list:
    ''' For a given set of addresses (or None for all addresses), builds a list of
        CoinsEntry tuples:
        
        CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change base_unit"))

    '''
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    coins = list()
    if wallet is None:
        utils.NSLog("get_coins: wallet was None, returning early")
        return coins
    c = wallet.get_utxos(domain, exclude_frozen, mature, confirmed_only)
    def get_name(x):
        return x.get('prevout_hash') + ":%d"%x.get('prevout_n')
    base_unit = parent.base_unit()
    for x in c:
        address = x['address']
        address_str = address.to_ui_string()
        height = x['height']
        name = get_name(x)
        tx_hash = x['prevout_hash']
        label = wallet.get_label(tx_hash)
        amount = x['value']
        amount_str = parent.format_amount(amount)
        is_frozen = wallet.is_frozen(address)
        is_change = wallet.is_change(address)
        entry = CoinsEntry(x, tx_hash, address, address_str, height, name, label, amount, amount_str, is_frozen, is_change, base_unit)
        coins.append(entry)
    
    coins.sort(key=lambda x: [x.address_str, x.amount, x.height], reverse=True)

    return coins

def empty_cell(cell : ObjCInstance, txt : str = "*Error*", italic : bool = False) -> ObjCInstance:
    if isinstance(cell, CoinsCell):
        cell.amount.text = ''
        cell.utxo.text = ''
        cell.flags.text = ''
        cell.desc.text = txt
        cell.address.text = ''
        cell.height.text = ''
        cell.tag = -1
        cell.onButton = None
        cell.chevronHidden = True
        cell.buttonSelected = False
    else:        
        cell.textLabel.attributedText = None
        cell.textLabel.text = txt
        if italic:
            cell.textLabel.font = UIFont.italicSystemFontOfSize_(cell.textLabel.font.pointSize)
        else:
            cell.textLabel.font = UIFont.systemFontOfSize_(cell.textLabel.font.pointSize)
        cell.detailTextLabel.attributedText = None
        cell.detailTextLabel.text = None
    cell.accessoryType = UITableViewCellAccessoryNone
    cell.accessoryView = None
    return cell


def toggle_freeze(entry) -> None:
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        entry = utils.set_namedtuple_field(entry, 'is_frozen', not entry.is_frozen)
        parent.wallet.set_frozen_state([entry.address], entry.is_frozen)
        parent.wallet.storage.write()
        parent.refresh_components('addresses')

def spend_from(coins: list) -> None:
    #print("SpendFrom")
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        parent.jump_to_send_with_spend_from(coins)

def PushCoinsVC(domain : list, navController : ObjCInstance) -> ObjCInstance:
    vc = CoinsTableVC.alloc()
    utils.nspy_put_byname(vc, domain, 'domain')
    vc = vc.initWithStyle_(UITableViewStylePlain).autorelease()
    navController.pushViewController_animated_(vc, True)
    return vc
