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

CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount_str amount is_frozen is_change")

CellIdentifiers = ( "CoinsCellLarge", "EmptyCell")

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
        self.tabBarItem.image = UIImage.imageNamed_("tab_coins.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
      
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

        gui.ElectrumGui.gui.sigCoins.connect(lambda: self.needUpdate(), self)

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
        nib = UINib.nibWithNibName_bundle_("CoinsCellLarge", None)
        self.tableView.registerNib_forCellReuseIdentifier_(nib, CellIdentifiers[0])
        self.refresh()
        
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        try:
            coins = utils.nspy_get_byname(self, 'coins')
            return len(coins) if coins else 1
        except:
            print("Error, exception retrieving coins from nspy cache")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        try:
            coins = utils.nspy_get_byname(self, 'coins')
            identifier = CellIdentifiers[0 if coins else -1]
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            parent = gui.ElectrumGui.gui
            if cell is None:
                cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            if coins:
                entry = coins[indexPath.row]
                setup_cell_for_coins_entry(cell, entry)
                cell.descTf.delegate = self
                cell.descTf.tag = indexPath.row
                cell.cpyBut.tag = indexPath.row
                cell.qrBut.tag = indexPath.row
                cell.addressGr.view.tag = indexPath.row
                cell.optionsBut.tag = indexPath.row
                if not cell.cpyBut.actionsForTarget_forControlEvent_(self,UIControlEventPrimaryActionTriggered):
                    cell.cpyBut.addTarget_action_forControlEvents_(self, SEL(b'onCpyBut:'), UIControlEventPrimaryActionTriggered)
                if not cell.qrBut.actionsForTarget_forControlEvent_(self,UIControlEventPrimaryActionTriggered):
                    cell.qrBut.addTarget_action_forControlEvents_(self, SEL(b'onQRBut:'), UIControlEventPrimaryActionTriggered)
                # According to UIGestureRecognizer docs, can call this multiple times and subsequent calls do nothing
                cell.addressGr.addTarget_action_(self,SEL(b'onOptions:'))
                if not cell.optionsBut.actionsForTarget_forControlEvent_(self,UIControlEventPrimaryActionTriggered):
                    cell.optionsBut.addTarget_action_forControlEvents_(self, SEL(b'onOptions:'), UIControlEventPrimaryActionTriggered)
                self.setupAccessoryForCell_atIndex_(cell, indexPath.row)
                    
            else:
                empty_cell(cell,_("No coins"),True)
        except Exception as e:
            utils.NSLog("exception in Coins tableView_cellForRowAtIndexPath_: %s",str(e))
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, CellIdentifiers[-1]).autorelease()
            empty_cell(cell)
        return cell
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def showTxDetailForIndex_(self, index : int) -> None:
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = utils.nspy_get_byname(self, 'coins')[index]
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
        tv.deselectRowAtIndexPath_animated_(indexPath,False)
        cell = tv.cellForRowAtIndexPath_(indexPath)

        coins = utils.nspy_get_byname(self, 'coins')
        if not coins or not len(coins): return

        self.setIndex_selected_(indexPath.row, not self.isIndexSelected_(indexPath.row))
        wasSel = self.setupAccessoryForCell_atIndex_(cell, indexPath.row) # this sometimes fails if address is frozen and/or we are watching only
        self.setIndex_selected_(indexPath.row, wasSel)

        self.selected = self.updateSelectionButtons()
        
 
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        return 150.0
        #return 44.0
   
    @objc_method
    def updateCoinsFromWallet(self):
        coins = get_coins(utils.nspy_get_byname(self, 'domain'))
        if coins is None:
            # probable backgroundeed and/or wallet is closed
            return
        utils.nspy_put_byname(self, coins, 'coins')
        utils.NSLog("fetched %d utxo entries from wallet (coins)",len(coins))

    @objc_method
    def refresh(self):
        self.needsRefresh = True # mark that a refresh was called in case refresh is blocked
        if self.blockRefresh:
            return
        self.updateCoinsFromWallet()
        if self.refreshControl: self.refreshControl.endRefreshing()
        self.selected = self.updateSelectionButtons()
        if self.tableView:
            self.tableView.reloadData()
        self.needsRefresh = False

    @objc_method
    def needUpdate(self):
        if self.needsRefresh: return
        self.needsRefresh = True
        self.retain()
        def inMain() -> None:
            self.doRefreshIfNeeded()
            self.autorelease()
        utils.do_in_main_thread(inMain)

    @objc_method
    def doRefreshIfNeeded(self):
        if self.needsRefresh:
            self.refresh()
            #print ("COINS REFRESHED")

                    
    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        tf.resignFirstResponder()
        return True

    @objc_method
    def textFieldDidBeginEditing_(self, tf) -> None:
        self.blockRefresh = True # temporarily block refreshing since that kills out keyboard/textfield
    
    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        coins = utils.nspy_get_byname(self, 'coins')
        if not coins or tf.tag < 0 or tf.tag >= len(coins):
            utils.NSLog("ERROR -- Coins label text field unknown tag: %d",int(tf.tag))
        else:
            entry = coins[tf.tag]
            newLabel = tf.text
            if newLabel != entry.label:
                # implicitly refreshes us
                gui.ElectrumGui.gui.on_label_edited(entry.tx_hash, newLabel)
        # need to enqueue a call to "doRefreshIfNeeded" because it's possible the user tapped another text field in which case we
        # don't want to refresh from underneath the user as that closes the keyboard, unfortunately
        # note we wait until here to unblock refresh because it's possible used tapped another textfield in the same view and we want to continue to block if that is the case
        self.blockRefresh = False # unblock block refreshing
        utils.call_later(0.250, lambda: self.doRefreshIfNeeded())

            
    @objc_method
    def onCpyBut_(self, but : ObjCInstance) -> None:
        #print ("On Copy But")
        try:
            entry = utils.nspy_get_byname(self, 'coins')[but.tag]
            gui.ElectrumGui.gui.copy_to_clipboard(entry.address_str, 'Address')
        except:
            import sys
            utils.NSLog("Exception during coins.py 'onCpyBut': %s",str(sys.exc_info()[1]))

    @objc_method
    def onQRBut_(self, but : ObjCInstance) -> None:
        #print ("On QR But")
        try:
            entry = utils.nspy_get_byname(self, 'coins')[but.tag]
            qrvc = utils.present_qrcode_vc_for_data(vc=self,
                                                    data=entry.address_str,
                                                    title = _('QR code'))
            gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)
            #print ("address =", entry.address_str)
        except:
            import sys
            utils.NSLog("Exception during coins.py 'onQRBut': %s",str(sys.exc_info()[1]))
            
    @objc_method
    def onOptions_(self, obj : ObjCInstance) -> None:
        #print ("On Options But")
        try:
            if isinstance(obj, UIGestureRecognizer):
                obj = obj.view
            entry = utils.nspy_get_byname(self, 'coins')[obj.tag]
            parent = gui.ElectrumGui.gui
            def on_block_explorer() -> None:
                parent.view_on_block_explorer(entry.tx_hash, 'tx')
            def on_request_payment() -> None:
                parent.jump_to_receive_with_address(entry.address)
            def on_address_details() -> None:                
                addrDetail = addresses.PushDetail(entry.address, self.navigationController)
            def spend_from2(utxos : list) -> None:
                validSels = list(self.updateSelectionButtons())
                coins = utils.nspy_get_byname(self, 'coins')
                for entry in coins:
                    if entry.name in validSels and entry.utxo not in utxos:
                        utxos.append(entry.utxo)
                if utxos:
                    spend_from(utxos)
    
            actions = [
                    [ _('Cancel') ],
                    [ _("Address Details"), on_address_details ],
                    [ _("Transaction Details"), lambda: self.showTxDetailForIndex_(obj.tag)],
                    [ _("View on block explorer"), on_block_explorer ],
                    [ _("Request payment"), on_request_payment ],
                ]
            
            watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True
    
            if not watch_only:
                actions.append([ _('Freeze') if not entry.is_frozen else _('Unfreeze'), lambda: toggle_freeze(entry) ])
    
            if not watch_only and not entry.is_frozen:
                actions.append([ _('Spend from this UTXO'), lambda: spend_from([entry.utxo]) ] )
                if len(list(self.updateSelectionButtons())):
                    actions.append([ _('Spend from this UTXO + Selected'), lambda: spend_from2([entry.utxo]) ] )
                    
                    
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
            entry = utils.nspy_get_byname(self, 'coins')[index]
            sels = set(list(self.selected))
            return bool(entry.name in sels)
        except:
            import sys
            utils.NSLog("Exception during coins.py 'isIndexSelected': %s",str(sys.exc_info()[1]))
        return False

    @objc_method
    def setIndex_selected_(self, index : int, b : bool) -> None:
        try:
            entry = utils.nspy_get_byname(self, 'coins')[index]
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
        coins = utils.nspy_get_byname(self, 'coins')
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
            coins = utils.nspy_get_byname(self, 'coins')
            for coin in coins:
                if not coin.is_frozen and coin.name in sels:
                    newSels.add(coin.name)
            if len(newSels):
                self.spendBut.enabled = True
            if len(sels):
                self.clearBut.enabled = True
        return ns_from_py(list(newSels))
    
    @objc_method
    def setupAccessoryForCell_atIndex_(self, cell, index : int) -> bool:
        parent = gui.ElectrumGui.gui
        no_good = parent.wallet is None or parent.wallet.is_watching_only()
        try:
            entry = utils.nspy_get_byname(self, 'coins')[index]
            if entry.is_frozen:
                no_good = True
        except:
            no_good = True
        
        ret = False
        
        if no_good or not self.isIndexSelected_(index):
            cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
            cell.accessoryView = get_circle_imageview()
        else:
            cell.accessoryType = UITableViewCellAccessoryCheckmark
            cell.accessoryView = None
            ret = True
        
        return ret


def setup_cell_for_coins_entry(cell : ObjCInstance, entry : CoinsEntry) -> None:
    if not isinstance(cell, CoinsCellLarge):
        empty_cell(cell)
        return
    #CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change")
    utxo, tx_hash, address, address_str, height, name, label, amount, amount_str, is_frozen, is_change, *dummy = entry

    if label is None:
        label = ''
        
    lblColor = UIColor.blackColor if not is_frozen else utils.uicolor_custom('frozen text')
    bgColor = UIColor.clearColor
    flags = list()
    if is_frozen:
        bgColor = utils.uicolor_custom('frozen')
        flags += [ _("Frozen") ]
    if is_change:
        bgColor = utils.uicolor_custom('change')
        flags += [ _("Change") ]

    cell.backgroundColor = bgColor

    cell.address.text = address_str
    cell.address.textColor = lblColor
    cell.descTf.placeholder = _("Description")
    cell.descTf.text = label
    cell.amt.font = utils.font_monospace_17_bold
    cell.amt.text = amount_str
    cell.utxo.text = name[0:10] + "\n... " + name[-2:]
    cell.utxo.font = utils.font_monospace_17_semibold
    cell.height.text = str(height)
    cell.flags.text = ", ".join(flags)
    
    if not cell.addressGr:
        cell.addressGr = UITapGestureRecognizer.new().autorelease()
        cell.address.addGestureRecognizer_(cell.addressGr)


    #cell.amt.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    #cell.utxo.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    
    cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
    cell.accessoryView = get_circle_imageview()
       
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
        
        CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change")

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
        entry = CoinsEntry(x, tx_hash, address, address_str, height, name, label, amount, amount_str, is_frozen, is_change)
        coins.append(entry)
    
    coins.sort(key=lambda x: [x.address_str, x.amount, x.height], reverse=True)

    return coins

def empty_cell(cell : ObjCInstance, txt : str = "*Error*", italic : bool = False) -> ObjCInstance:
    if isinstance(cell, CoinsCellLarge):
        cell.amt.text = ''
        cell.utxo.text = ''
        cell.flags.text = ''
        cell.descTf.text = txt
        cell.address.text = txt
        cell.height.text = ''
        cell.tag = -1
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

def get_circle_imageview() -> ObjCInstance:
    iv = UIImageView.alloc().initWithImage_(UIImage.imageNamed_("circle.png")).autorelease()
    iv.frame = CGRectMake(0,0,24,24)
    iv.contentMode = UIViewContentModeScaleAspectFit
    return iv

def PushCoinsVC(domain : list, navController : ObjCInstance) -> ObjCInstance:
    vc = CoinsTableVC.alloc()
    utils.nspy_put_byname(vc, domain, 'domain')
    vc = vc.initWithStyle_(UITableViewStylePlain).autorelease()
    navController.pushViewController_animated_(vc, True)
    return vc
