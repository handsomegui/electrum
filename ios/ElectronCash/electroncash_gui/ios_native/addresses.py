from . import utils
from . import gui
from . import history
from . import private_key_dialog
from . import sign_decrypt_dialog
from .txdetail import TxDetail
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
import electroncash.exchange_rate
from electroncash.i18n import _, language
from electroncash.address import Address

import time
import html
import sys
from collections import namedtuple

from .uikit_bindings import *
from .custom_objc import *


class AddressDetail(UIViewController):
    
    defaultBG = objc_property()
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.title = "Address Details"
        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("AddressDetail dealloc")
        utils.nspy_pop(self)
        self.title = None
        self.view = None
        self.defaultBG = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("AddressDetail",None,None)
        v = None
        gr = None
        
        for o in objs:
            if isinstance(o, UIView):
                v = o
            elif isinstance(o, UIGestureRecognizer):
                gr = o
        if v is None or gr is None:
            raise ValueError('AddressDetail XIB is missing either the primary view or the expected gesture recognizer!')
        
        gr.addTarget_action_(self, SEL(b'onTapAddress'))

        parent = gui.ElectrumGui.gui
   
        entry = utils.nspy_get_byname(self, 'entry')        

        tf = v.viewWithTag_(210)
        tf.delegate = self

        but = v.viewWithTag_(520)
        def toggleFreeze(oid : objc_id) -> None:
            self.onToggleFreeze()
        but.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, toggleFreeze)
        
        butMore = v.viewWithTag_(150)
        def onButMore(oid : objc_id) -> None:
            self.onTapAddress()
        butMore.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onButMore)

        butCpy = v.viewWithTag_(120)
        butQR = v.viewWithTag_(130)
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        def onCpy(oid : objc_id) -> None:
            self.onCpyBut()
        def onQR(oid : objc_id) -> None:
            self.onQRBut()
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCpy) # bind actin to closure 
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onQR)  # bind action to closure
        
        utils.nspy_put_byname(self, history.get_history([entry.address]), 'history')
        tv = v.viewWithTag_(1000)
        tv.delegate = self
        tv.dataSource = self

        self.view = v
                
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.refresh()
        
    @objc_method
    def refresh(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        entry = utils.nspy_get_byname(self, 'entry')
 
        lbl = v.viewWithTag_(100)
        lbl.text = _("Address") + ":"        
        lbl = v.viewWithTag_(110)
        lbl.text = entry.addr_str
        bgColor = None
        if self.defaultBG is None:
            self.defaultBG = lbl.backgroundColor
        lbl.textColor = UIColor.blackColor 
        if entry.is_change:
            lbl.backgroundColor = utils.uicolor_custom('change address')
            if entry.is_frozen:
                lbl.textColor = utils.uicolor_custom('frozen address text')
        elif entry.is_frozen:
            lbl.backgroundColor = utils.uicolor_custom('frozen address')
        else:
            lbl.backgroundColor = self.defaultBG
        bgColor = lbl.backgroundColor
        lbl = v.viewWithTag_(200)
        lbl.text = _("Description") + ":"
        tf = v.viewWithTag_(210)
        tf.placeholder = _("Tap to add a description")
        tf.text = entry.label

        lbl = v.viewWithTag_(300)
        lbl.text = _("NumTx") + ":"
        lbl = v.viewWithTag_(310)
        lbl.text = str(entry.num_tx)
        
        lbl = v.viewWithTag_(400)
        lbl.text = _("Balance") + ":"
        lbl = v.viewWithTag_(410)
        lbl.text = entry.balance_str + ((' (' + entry.fiat_balance_str + ')') if entry.fiat_balance_str else '')
        
        lbl = v.viewWithTag_(500)
        lbl.text = _("Flags") + ":"
        lbl = v.viewWithTag_(510)
        flags = []
        if entry.is_change: flags.append(_("Change"))
        if entry.is_frozen: flags.append(_("Frozen"))
        lbl.text = ', '.join(flags)
        
        tv = v.viewWithTag_(1000)
        tv.backgroundColor = bgColor
        utils.nspy_put_byname(self, history.get_history([entry.address]), 'history')
        
        self.refreshButs()
        tv.reloadData()
        
    @objc_method
    def onTapAddress(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        parent = gui.ElectrumGui.gui
        def on_block_explorer() -> None:
            parent.view_on_block_explorer(entry.address, 'addr')
        def on_request_payment() -> None:
            parent.jump_to_receive_with_address(entry.address)
        def on_private_key() -> None:
            def onPw(password : str) -> None:
                # present the private key view controller here.
                pk = None
                try:
                    pk = parent.wallet.export_private_key(entry.address, password) if parent.wallet else None
                except Exception as e:
                    parent.show_error(str(e))
                    return
                if pk:
                    vc = private_key_dialog.PrivateKeyDialog.alloc().init().autorelease()
                    pkentry = private_key_dialog.PrivateKeyEntry(entry.address, pk, entry.is_frozen, entry.is_change)
                    utils.nspy_put_byname(vc, pkentry, 'entry')
                    self.navigationController.pushViewController_animated_(vc, True)
            parent.prompt_password_if_needed_asynch(onPw)
        def on_sign_verify() -> None:
            vc = sign_decrypt_dialog.Create_SignVerify_VC(entry.address)
            self.navigationController.pushViewController_animated_(vc, True)

        def on_encrypt_decrypt() -> None:
            if not parent.wallet: return
            try:
                pubkey = parent.wallet.get_public_key(entry.address)
            except:
                print("exception extracting public key:",str(sys.exc_info()[1]))
                return
            if pubkey is not None and not isinstance(pubkey, str):
                pubkey = pubkey.to_ui_string()
            if not pubkey:
                return
            vc = sign_decrypt_dialog.Create_EncryptDecrypt_VC(entry.address, pubkey)
            self.navigationController.pushViewController_animated_(vc, True)

        actions = [
                [ _('Cancel') ],
                #[ _('Copy to clipboard'), lambda: self.onCpyBut() ],
                #[ _('Show as QR code'), lambda: self.onQRBut() ],
                [ _("View on block explorer"), on_block_explorer ],
                [ _("Request payment"), on_request_payment ],
            ]
        
        watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True

        if not watch_only:
            actions.append([ _('Freeze') if not entry.is_frozen else _('Unfreeze'), lambda: self.onToggleFreeze() ])

        if not watch_only and not entry.is_frozen and entry.balance > 0:
            actions.append([ _('Spend from this Address'), lambda: self.doSpendFrom() ] )

        if not watch_only:
            actions.append([ _('Private key'), on_private_key ] )
            
        if not watch_only and entry.address.kind == entry.address.ADDR_P2PKH:
            actions.append([ _('Sign/verify Message'), on_sign_verify ] )
            actions.append([ _('Encrypt/decrypt Message'), on_encrypt_decrypt ] )
            
        utils.show_alert(
            vc = self,
            title = _("Options"),
            message = _("Address") + ":" + " " + entry.addr_str[0:12] + "..." + entry.addr_str[-12:],
            actions = actions,
            cancel = _('Cancel'),
            style = UIAlertControllerStyleActionSheet
        )
    @objc_method
    def onCpyBut(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        UIPasteboard.generalPasteboard.string = entry.addr_str
        utils.show_notification(message=_("Text copied to clipboard"))
    @objc_method
    def onQRBut(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        qrvc = utils.present_qrcode_vc_for_data(vc=self.tabBarController,
                                                data=entry.addr_str,
                                                title = _('QR code'))
        gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)

    @objc_method
    def onToggleFreeze(self) -> None:
        parent = gui.ElectrumGui.gui
        if parent.wallet:
            entry = utils.nspy_get_byname(self, 'entry')
            entry = utils.set_namedtuple_field(entry, 'is_frozen', not entry.is_frozen)
            utils.nspy_put_byname(self, entry, 'entry')
            parent.wallet.set_frozen_state([entry.address], entry.is_frozen)
            parent.wallet.storage.write()
            parent.refresh_components('addresses')
            self.refresh()

    @objc_method
    def doSpendFrom(self) -> None:
        parent = gui.ElectrumGui.gui
        if parent.wallet:
            entry = utils.nspy_get_byname(self, 'entry')
            coins = parent.wallet.get_spendable_coins([entry.address], parent.config)
            if coins:
                parent.jump_to_send_with_spend_from(coins)
        
    @objc_method
    def refreshButs(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        parent = gui.ElectrumGui.gui
        watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True
        but = v.viewWithTag_(520)
        entry = utils.nspy_get_byname(self, 'entry')
        but.setTitle_forState_(_("Freeze") if not entry.is_frozen else _("Unfreeze"), UIControlStateNormal)
        but.setHidden_(watch_only)

        but = v.viewWithTag_(150)
        but.setTitle_forState_(_("Options") + "...", UIControlStateNormal)
        

    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        #print("hit return, value is {}".format(tf.text))
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidBeginEditing_(self, tf) -> None:
        #self.blockRefresh = True # temporarily block refreshing since that kills out keyboard/textfield
        pass

    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        
        tf.text = tf.text.strip()
        new_label = tf.text
        entry = utils.set_namedtuple_field(entry, 'label', new_label)
        utils.nspy_put_byname(self, entry, 'entry')
        print ("new label for address %s = %s"%(entry.address.to_storage_string(), new_label))
        gui.ElectrumGui.gui.on_label_edited(entry.address, new_label)
        #self.blockRefresh = False # unblock block refreshing
        #utils.call_later(0.250, lambda: self.refresh())
        self.refresh()
        
    @objc_method
    def tableView_numberOfRowsInSection_(self, tv, section : int) -> int:
        h = utils.nspy_get_byname(self, 'history')
        return len(h) if h else 1
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv, section : int) -> ObjCInstance:
        return _("Transaction History")
    
    @objc_method
    def numberOfSectionsInTableView_(self, tv) -> int:
        return 1
    
    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tv, indexPath) -> ObjCInstance:
        identifier = str(__class__)
        cell = tv.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            cell.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(1.0,1.0,1.0,0.7)
        try:
            hstry = utils.nspy_get_byname(self, 'history')
            if hstry and len(hstry):
                cell.opaque = False
                hentry = hstry[indexPath.row]
                history.setup_cell_for_history_entry(cell, hentry)
            else:
                history.empty_cell(cell, _("No transactions"), True)
        except Exception as e:
            print("exception in AddressDetail.tableView_cellForRowAtIndexPath_: %s"%str(e))
            history.empty_cell(cell)
        return cell

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath) -> None:
        #print("DID SELECT ROW CALLED FOR ROW %d"%indexPath.row)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = utils.nspy_get_byname(self, 'history')[indexPath.row]
        except:
            tv.deselectRowAtIndexPath_animated_(indexPath,True)
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        rawtx = None
        if tx is not None: rawtx = tx.raw
        else: return
        txd = TxDetail.alloc()
        utils.nspy_put_byname(txd, entry, 'tx_entry')
        self.navigationController.pushViewController_animated_(txd.initWithRawTx_(rawtx).autorelease(), True)

AddressesTableVCModeNormal = 0
AddressesTableVCModePicker = 1

# Addresses Tab -- shows addresses, etc
class AddressesTableVC(UITableViewController):
    needsRefresh = objc_property()
    blockRefresh = objc_property()
    mode = objc_property()

    @objc_method
    def initWithMode_(self, mode : int):
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', UITableViewStylePlain, argtypes=[c_int]))
        self.needsRefresh = False
        self.blockRefresh = False
        self.mode = int(mode)
        self.title = _("&Addresses").split('&')[1] if self.mode == AddressesTableVCModeNormal else _("Choose Address")

        self.refreshControl = UIRefreshControl.alloc().init().autorelease() 
        self.updateAddressesFromWallet()
        
        if self.mode == AddressesTableVCModePicker:
            def onRefreshCtl() -> None:
                self.refresh()
            self.refreshControl.handleControlEvent_withBlock_(UIControlEventValueChanged, onRefreshCtl)
        
        return self

    @objc_method
    def dealloc(self) -> None:
        self.needsRefresh = None
        self.mode = None
        self.blockRefresh = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def loadView(self) -> None:
        # frame is pretty much ignored due to autosizie but c'tor needs it...
        self.tableView = CollapsableTableView.alloc().initWithFrame_style_(CGRectMake(0,0,320,600), UITableViewStylePlain).autorelease()
        if self.mode == AddressesTableVCModeNormal:
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
        identifier = str(__class__) if self.mode == AddressesTableVCModeNormal else "Cell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        newCell = False
        if self.mode == AddressesTableVCModePicker and cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle,identifier).autorelease()
            newCell = True
        assert cell is not None

        addrData = utils.nspy_get_byname(self, 'addrData')
        entries = addrData.getSections().get(indexPath.section,(None,[]))[1]
        assert indexPath.row < len(entries)
        entry = entries[indexPath.row]
        if self.mode == AddressesTableVCModeNormal:
            addrlbl = cell.viewWithTag_(10)
            chglbl = cell.viewWithTag_(15)
            addrlbl.text = entry.addr_str
            ballbl = cell.viewWithTag_(20)
            ballbl.text = entry.balance_str + ( (' (' + entry.fiat_balance_str + ')') if addrData.show_fx else '')
            ballbl.font = UIFont.monospacedDigitSystemFontOfSize_weight_(UIFont.labelFontSize(), UIFontWeightLight if not entry.balance else UIFontWeightSemibold )
            numlbl = cell.viewWithTag_(30)
            numlbl.text = str(entry.num_tx)
            numlbl.font = UIFont.monospacedDigitSystemFontOfSize_weight_(UIFont.labelFontSize(), UIFontWeightLight if not entry.num_tx else UIFontWeightSemibold)
            tf = cell.viewWithTag_(40)
            tf.text = entry.label if entry.label else ""
            tf.placeholder = _("Tap to add a description")
            cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
    
            xtra = []
            bgcolor = UIColor.clearColor        
            if entry.is_frozen:
                xtra += [_("Frozen")]
                bgcolor = utils.uicolor_custom('frozen address')            
            if entry.is_change:
                xtra.insert(0, _("Change"))
                bgcolor = utils.uicolor_custom('change address')
    
            cell.backgroundColor = bgcolor
            if xtra:
                chglbl.setHidden_(False)
                chglbl.text = ", ".join(xtra)
            else:
                chglbl.text = ""
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
        else: # picker mode
            if newCell: 
                cell.accessoryType = UITableViewCellAccessoryNone
                cell.textLabel.adjustsFontSizeToFitWidth = True
                cell.textLabel.minimumScaleFactor = 0.9
                font = cell.textLabel.font
                cell.textLabel.font = UIFont.boldSystemFontOfSize_(font.pointSize)
                cell.detailTextLabel.adjustsFontSizeToFitWidth = True
                cell.detailTextLabel.minimumScaleFactor = 0.85
            cell.textLabel.text = str(entry.address)
            cell.detailTextLabel.text = "bal: " + entry.balance_str + ( (' (' + entry.fiat_balance_str + ')') if addrData.show_fx else '') + " numtx: " + str(entry.num_tx) + ((" - " + entry.label) if entry.label else "")
            cell.backgroundColor = tableView.backgroundColor
            cell.textLabel.textColor = UIColor.darkTextColor
            if entry.is_frozen:
                cell.backgroundColor = utils.uicolor_custom('frozen address')
                cell.textLabel.textColor = utils.uicolor_custom('frozen address text')
            if entry.is_change:
                cell.backgroundColor = utils.uicolor_custom('change address')                

        return cell
    
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        if self.mode == AddressesTableVCModeNormal:
            return 126.0
        return 44.0
    
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
                if self.mode == AddressesTableVCModeNormal:
                    addrDetail = AddressDetail.alloc().init().autorelease()
                    utils.nspy_put_byname(addrDetail, entry, 'entry')
                    self.navigationController.pushViewController_animated_(addrDetail, True)
                else:
                    cb = utils.get_callback(self, 'on_picked')
                    if callable(cb): cb(entry)
    
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
                balance_text = self.parent.format_amount(balance, whitespaces=False)
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


def present_modal_address_picker(callback) -> None:
    parent = gui.ElectrumGui.gui
    avc = AddressesTableVC.alloc().initWithMode_(AddressesTableVCModePicker).autorelease()
    nav = UINavigationController.alloc().initWithRootViewController_(avc).autorelease()
    def pickedAddress(entry) -> None:
        if callable(callback):
            callback(entry)
        nav.presentingViewController.dismissViewControllerAnimated_completion_(True, None)
    utils.add_callback(avc, 'on_picked', pickedAddress)
    parent.add_navigation_bar_close_to_modal_vc(avc)
    parent.get_presented_viewcontroller().presentViewController_animated_completion_(nav, True, None)
