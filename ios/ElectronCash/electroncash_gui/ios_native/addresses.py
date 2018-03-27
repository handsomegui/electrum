from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
import electroncash.exchange_rate
from electroncash.i18n import _, language
from electroncash.address import Address

import time
import html
from collections import namedtuple

from .uikit_bindings import *
from .custom_objc import *


class AddressDetail(UIViewController):
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.title = "Address Information"
        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("AddressDetail dealloc")
        utils.nspy_pop(self)
        self.title = None
        self.view = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        self.view = UIView.alloc().init().autorelease()
        lbl = UILabel.alloc().init().autorelease()
        entry = utils.nspy_get(self)
        if entry:
            lbl.text = "Address Detail: " + str(entry.addr_idx) + " " + entry.addr_str + " "
        lbl.adjustsFontSizeForWidth = True
        lbl.numberOfLines = 2
        w = UIScreen.mainScreen.bounds.size.width
        rect = CGRectMake(0,100,w,80)
        lbl.frame = rect
        self.view.addSubview_(lbl)

 
# Addresses Tab -- shows addresses, etc
class AddressesTableVC(UITableViewController):
    needsRefresh = objc_property()
    blockRefresh = objc_property()
    style = objc_property()

    @objc_method
    def initWithStyle_(self, style : int):
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
        self.blockRefresh = False
        self.style = style
        self.title = _("&Addresses").split('&')[1]
                
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()
        self.updateAddressesFromWallet()
        
        return self

    @objc_method
    def dealloc(self) -> None:
        self.needsRefresh = None
        self.style = None
        self.blockRefresh = None
        utils.nspy_pop(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def loadView(self) -> None:
        # frame is pretty much ignored due to autosizie but c'tor needs it...
        self.tableView = CollapsableTableView.alloc().initWithFrame_style_(CGRectMake(0,0,320,600), self.style).autorelease()
        uinib = UINib.nibWithNibName_bundle_("AddressListCell", None)
        self.tableView.registerNib_forCellReuseIdentifier_(uinib, str(__class__))


    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        addrData = utils.nspy_get_byname(self, 'addrData')
        return len(addrData.getSections()) if addrData is not None else 0
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance,section : int) -> ObjCInstance:
        try:
            addrData = utils.nspy_get_byname(self, 'addrData')
            return addrData.getSections().get(section, ('',None))[0]
        except Exception as e:
            print("Error in addresses 1: %s"%str(e))
            return '*Error*'
            
    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView : ObjCInstance, section : int) -> int:
        try:
            addrData = utils.nspy_get_byname(self, 'addrData')
            d = addrData.getSections()
            return len(d.get(section,(None,[]))[1])
        except Exception as e:
            print("Error in addresses 2: %s"%str(e))
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        #todo: - allow for label editing (popup menu?)
        identifier = str(__class__)
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        assert cell is not None

        addrData = utils.nspy_get_byname(self, 'addrData')
        entries = addrData.getSections().get(indexPath.section,(None,[]))[1]
        assert indexPath.row < len(entries)
        entry = entries[indexPath.row]
        addrlbl = cell.viewWithTag_(10)
        chglbl = cell.viewWithTag_(15)
        addrlbl.text = entry.addr_str
        ballbl = cell.viewWithTag_(20)
        ballbl.text = entry.balance_str + ( ('(' + entry.fiat_balance_str + ')') if addrData.show_fx else '')
        ballbl.font = UIFont.monospacedDigitSystemFontOfSize_weight_(UIFont.labelFontSize(), UIFontWeightLight if not entry.balance else UIFontWeightSemibold )
        numlbl = cell.viewWithTag_(30)
        numlbl.text = str(entry.num_tx)
        numlbl.font = UIFont.monospacedDigitSystemFontOfSize_weight_(UIFont.labelFontSize(), UIFontWeightLight if not entry.num_tx else UIFontWeightSemibold)
        tf = cell.viewWithTag_(40)
        tf.text = entry.label if entry.label else ""
        tf.placeholder = _("Tap to add a description")
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
        if entry.is_change:
            cell.backgroundColor = utils.uicolor_custom('change address')
            chglbl.setHidden_(False)
            chglbl.text = _("Change")
        else:
            cell.backgroundColor = UIColor.clearColor
            chglbl.setHidden_(True)
        butCpy = cell.viewWithTag_(120)
        butQR = cell.viewWithTag_(130)
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        closure_address = entry.addr_str
        def onCpy(oid : objc_id) -> None:
            UIPasteboard.generalPasteboard.string = closure_address
            utils.show_notification(message=_("Text copied to clipboard"))
        def onQR(oid : objc_id) -> None:
            qrvc = utils.present_qrcode_vc_for_data(vc=self.tabBarController,
                                                    data=closure_address,
                                                    title = _('QR code'))
            gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCpy) # bind actin to closure 
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onQR)  # bind action to closure

        tf.delegate = self
        d = utils.nspy_get_byname(self, 'tf_dict')
        d = d if d else dict()
        d[tf.ptr.value] = entry.address
        utils.nspy_put_byname(self, d, 'tf_dict')

        return cell
    
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        return 126.0
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR SECTION %s, ROW %s"%(str(indexPath.section),str(indexPath.row)))
        addrData = utils.nspy_get_byname(self, 'addrData')
        if addrData is not None:
            section = addrData.getSections().get(indexPath.section,None)
            if section is not None and indexPath.row < len(section[1]):
                entry = section[1][indexPath.row]
                addrDetail = AddressDetail.alloc().init().autorelease()
                utils.nspy_put(addrDetail, entry)
                self.navigationController.pushViewController_animated_(addrDetail, True)
    
    @objc_method
    def updateAddressesFromWallet(self):
        addrData = utils.nspy_get_byname(self, 'addrData')
        if addrData is None:
            addrData = AddressData(gui.ElectrumGui.gui)
        addrData.refresh()
        utils.nspy_put_byname(self, addrData, 'addrData')

    @objc_method
    def refresh(self):
        self.needsRefresh = True # mark that a refresh was called in case refresh is blocked
        if self.blockRefresh:
            return
        self.updateAddressesFromWallet()
        if self.refreshControl: self.refreshControl.endRefreshing()
        if self.tableView: 
            self.tableView.reloadData()
        #print("did address refresh")
        self.needsRefresh = False # indicate refreshing done

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
            #print ("ADDRESSES REFRESHED")


    @objc_method
    def showRefreshControl(self):
        if self.refreshControl is not None and not self.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            self.refreshControl.beginRefreshing()
            self.tableView.setContentOffset_animated_(CGPointMake(0, self.tableView.contentOffset.y-self.refreshControl.frame.size.height), True)

    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        #print("hit return, value is {}".format(tf.text))
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidBeginEditing_(self, tf) -> None:
        self.blockRefresh = True # temporarily block refreshing since that kills out keyboard/textfield

    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        address = utils.nspy_get_byname(self, 'tf_dict').get(tf.ptr.value, None)
        
        tf.text = tf.text.strip()
        new_label = tf.text
        print ("new label for address %s = %s"%(address.to_storage_string(), new_label))
        gui.ElectrumGui.gui.on_label_edited(address, new_label)
        self.blockRefresh = False # unblock block refreshing
        # need to enqueue a call to "doRefreshIfNeeded" because it's possible the user tapped another text field in which case we
        # don't want to refresh from underneath the user as that closes the keyboard, unfortunately
        utils.call_later(0.250, lambda: self.doRefreshIfNeeded())

class AddressData:
    
    Entry = namedtuple("Entry", "address addr_str addr_idx label balance_str fiat_balance_str num_tx is_frozen balance is_change is_used")
    
    def __init__(self, gui_parent):
        self.parent = gui_parent
        self.clear()
        
    def clear(self):
        self.receiving = list()
        self.used = list()
        self.unspent = list()
        self.change = list()
        self.sections = dict()
        self.show_fx = False
        
    def refresh(self):
        self.clear()
        wallet = self.parent.wallet
        daemon = self.parent.daemon
        if wallet is None: return
        receiving_addresses = wallet.get_receiving_addresses()
        change_addresses = wallet.get_change_addresses()

        if daemon and daemon.fx and daemon.fx.get_fiat_address_config():
            fx = daemon.fx
            self.show_fx = True
        else:
            self.show_fx = False
            fx = None
        which_list = self.unspent
        sequences = [0,1] if change_addresses else [0]
        for is_change in sequences:
            if len(sequences) > 1:
                which_list = self.receiving if not is_change else self.change
            else:
                which_list = self.unspent
            addr_list = change_addresses if is_change else receiving_addresses
            for n, address in enumerate(addr_list):
                num = len(wallet.get_address_history(address))
                is_used = wallet.is_used(address)
                balance = sum(wallet.get_addr_balance(address))
                address_text = address.to_ui_string()
                label = wallet.labels.get(address.to_storage_string(), '')
                balance_text = self.parent.format_amount(balance, whitespaces=True)
                is_frozen = wallet.is_frozen(address)
                fiat_balance = (fx.value_str(balance, fx.exchange_rate()) + " " + fx.get_currency()) if fx else ""
                #Entry = "address addr_str addr_idx, label, balance_str, fiat_balance_str, num_tx, is_frozen, balance, is_change, is_used"
                item = AddressData.Entry(address, address_text, n, label, balance_text, fiat_balance, num,
                                         bool(is_frozen), balance, bool(is_change), bool(is_used))
                if is_used:
                    self.used.append(item)
                else:
                    if balance <= 0.0 and len(sequences) < 2:
                        self.receiving.append(item)
                    else:
                        if balance > 0.0:
                            self.unspent.append(item)
                        else:
                            which_list.append(item)
        
        self.used.sort(key=lambda x: [x.balance,x.num_tx,0-x.addr_idx], reverse=True )
        self.change.sort(key=lambda x: [x.balance,x.num_tx,0-x.addr_idx], reverse=True )
        self.unspent.sort(key=lambda x: [x.balance,x.num_tx,0-x.addr_idx], reverse=True )
        self.receiving.sort(key=lambda x: [x.balance,x.num_tx,0-x.addr_idx], reverse=True )
        
                    
    def getSections(self) -> dict:
        if len(self.sections):
            return self.sections
        d = {}
        if len(self.unspent):
            d[len(d)] = (_("Unspent"), self.unspent)
        d[len(d)] = (_("Receiving"), self.receiving)
        if len(self.used):
            d[len(d)] = (_("Used"), self.used)
        if len(self.change):
            d[len(d)] = (_("Change"), self.change)
        self.sections = d
        return d
