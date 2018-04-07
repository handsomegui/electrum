from . import utils
from . import gui
from .txdetail import TxDetail
from .addresses import AddressDetail
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *
from .custom_objc import *
from collections import namedtuple

CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount_str amount is_frozen is_change")

CellIdentifiers = ( "CoinsCellLarge", "EmptyCell")

class CoinsTableVC(UITableViewController):
    ''' Coins Tab -- shows utxos
    '''
    needsRefresh = objc_property()

    @objc_method
    def initWithStyle_(self, style : int) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
        self.title = _("Coins")
        self.tabBarItem.image = UIImage.imageNamed_("tab_coins.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
        
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()

        return self

    @objc_method
    def dealloc(self) -> None:
        self.needsRefresh = None
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
            print("Error, no coins in nspy cache")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        try:
            coins = utils.nspy_get_byname(self, 'coins')
            identifier = CellIdentifiers[0 if coins else -1]
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
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
                
            else:
                empty_cell(cell,_("No coins"),True)
        except Exception as e:
            print("exception in Coins tableView_cellForRowAtIndexPath_: %s"%str(e))
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, CellIdentifiers[-1]).autorelease()
            empty_cell(cell)
        return cell
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR ROW %d"%indexPath.row)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = utils.nspy_get_byname(self, 'coins')[indexPath.row]
            hentry = parent.get_history_entry(entry.tx_hash)
            if hentry is None: raise Exception("NoHEntry")
        except:
            tv.deselectRowAtIndexPath_animated_(indexPath,True)
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        rawtx = None
        if tx is not None: rawtx = tx.raw
        txd = TxDetail.alloc()
        utils.nspy_put_byname(txd, hentry, 'tx_entry')
        self.navigationController.pushViewController_animated_(txd.initWithRawTx_(rawtx).autorelease(), True)
 
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        return 150.0
        #return 44.0
   
    @objc_method
    def updateCoinsFromWallet(self):
        coins = get_coins()
        if coins is None:
            # probable backgroundeed and/or wallet is closed
            return
        utils.nspy_put_byname(self, coins, 'coins')
        print ("fetched %d utxo entries from wallet (coins)"%len(coins))

    @objc_method
    def refresh(self):
        self.updateCoinsFromWallet()
        if self.refreshControl: self.refreshControl.endRefreshing()
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

    # This method runs in the main thread as it's enqueue using our hacky "Heartbeat" mechanism/workaround for iOS
    @objc_method
    def doRefreshIfNeeded(self):
        if self.needsRefresh:
            self.refresh()
            #print ("COINS REFRESHED")

    @objc_method
    def showRefreshControl(self):
        if self.refreshControl is not None and not self.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            self.refreshControl.beginRefreshing()
            self.tableView.setContentOffset_animated_(CGPointMake(0, self.tableView.contentOffset.y-self.refreshControl.frame.size.height), True)
                    
    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        coins = utils.nspy_get_byname(self, 'coins')
        if not coins or tf.tag < 0 or tf.tag >= len(coins):
            utils.NSLog("ERROR -- Coins label text field unknown tag: %d",int(tf.tag))
            return
        entry = coins[tf.tag]
        newLabel = tf.text
        if newLabel != entry.label:
            gui.ElectrumGui.gui.on_label_edited(entry.tx_hash, newLabel)
            
    @objc_method
    def onCpyBut_(self, but : ObjCInstance) -> None:
        #print ("On Copy But")
        try:
            entry = utils.nspy_get_byname(self, 'coins')[but.tag]
            UIPasteboard.generalPasteboard.string = entry.address_str
            #print ("address =", entry.address_str)
            utils.show_notification(message=_("Text copied to clipboard"))
        except:
            import sys
            utils.NSLog("Exception during 'onCpyBut': %s",str(sys.exc_info()[1]))

    @objc_method
    def onQRBut_(self, but : ObjCInstance) -> None:
        #print ("On QR But")
        try:
            entry = utils.nspy_get_byname(self, 'coins')[but.tag]
            qrvc = utils.present_qrcode_vc_for_data(vc=self.tabBarController,
                                                    data=entry.address_str,
                                                    title = _('QR code'))
            gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)
            #print ("address =", entry.address_str)
        except:
            import sys
            utils.NSLog("Exception during 'onQRBut': %s",str(sys.exc_info()[1]))
            
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
                aentry = parent.get_address_entry(entry.address)
                if aentry:
                    addrDetail = AddressDetail.alloc().init().autorelease()
                    utils.nspy_put_byname(addrDetail, aentry, 'entry')
                    self.navigationController.pushViewController_animated_(addrDetail, True)
    
            actions = [
                    [ _('Cancel') ],
                    [ _("Address Details"), on_address_details ],
                    [ _("Transaction Details"), lambda: self.tableView_didSelectRowAtIndexPath_(self.tableView,NSIndexPath.indexPathForRow_inSection_(obj.tag,0))],
                    [ _("View on block explorer"), on_block_explorer ],
                    [ _("Request payment"), on_request_payment ],
                ]
            
            watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True
    
            if not watch_only:
                actions.append([ _('Freeze') if not entry.is_frozen else _('Unfreeze'), lambda: toggle_freeze(entry) ])
    
            if not watch_only and not entry.is_frozen:
                actions.append([ _('Spend from this UTXO'), lambda: spend_from(entry) ] )
                    
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
            utils.NSLog("Exception during 'onOptions': %s",str(sys.exc_info()[1]))
    


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
    cell.amt.text = amount_str
    cell.utxo.text = name[0:10] + "\n... " + name[-2:]
    cell.height.text = str(height)
    cell.flags.text = ", ".join(flags)
    
    if not cell.addressGr:
        cell.addressGr = UITapGestureRecognizer.new().autorelease()
        cell.address.addGestureRecognizer_(cell.addressGr)


    #cell.amt.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    #cell.utxo.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    
    cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
       

def get_coins(domain : list = None, exclude_frozen : bool = False, mature : bool = False, confirmed_only : bool = False) -> list:
    ''' For a given set of addresses (or None for all addresses), builds a list of
        CoinsEntry tuples:
        
        CoinsEntry = namedtuple("CoinsEntry", "utxo tx_hash address address_str height name label amount amount_str is_frozen is_change")

        '''
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    if wallet is None:
        utils.NSLog("get_coins: wallent was None, returning early")
        return None
    c = wallet.get_utxos(domain, exclude_frozen, mature, confirmed_only)
    coins = list()
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
    return cell


def toggle_freeze(entry) -> None:
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        entry = utils.set_namedtuple_field(entry, 'is_frozen', not entry.is_frozen)
        parent.wallet.set_frozen_state([entry.address], entry.is_frozen)
        parent.wallet.storage.write()
        parent.refresh_components('addresses')

def spend_from(entry) -> None:
    print("SpendFrom: ",entry.name)
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        parent.jump_to_send_with_spend_from([entry.utxo])