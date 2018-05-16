from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
from .coins import get_circle_imageview
from electroncash.address import Address, PublicKey
from .uikit_bindings import *
from .custom_objc import *
from collections import namedtuple
import time

ContactsEntry = namedtuple("ContactsEntry", "name address address_str tx_hashes")

CellIdentifiers = ( "Cell", "EmptyCell")

ModeNormal = 0
ModePicker = 1

class ContactsTableVC(UITableViewController):
    ''' Contacts Tab -- shows named contacts (association of a user-friendly name and an address)
    '''
    needsRefresh = objc_property()
    blockRefresh = objc_property()
    addBut = objc_property()
    doneBut = objc_property()
    cancelBut = objc_property()
    mode = objc_property()
    selected = objc_property()
    

    @objc_method
    def commonInitWithMode_(self, mode : int) -> None:
        self.needsRefresh = False
        self.blockRefresh = False
        self.mode = ModeNormal if mode == ModeNormal else ModePicker
        self.title = _("Contacts")
        self.selected = []
        self.tabBarItem.image = UIImage.imageNamed_("tab_contacts.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
        self.addBut = None
        self.doneBut = None
        self.cancelBut = None
      
        if self.mode == ModePicker:
            lbuts = [
                UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemStop, self, SEL(b'onPickerCancel')).autorelease(),
            ]
            buts = [
                UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemDone, self, SEL(b'onPickerPayTo')).autorelease(),
                UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemAdd, self, SEL(b'onAddBut')).autorelease(),
            ]
            self.cancelBut = lbuts[0]
            self.doneBut = buts[0]
            self.addBut = buts[1]
            self.doneBut.enabled = False
            self.cancelBut.enabled = True
            self.navigationItem.rightBarButtonItems = buts
            self.navigationItem.leftBarButtonItems = lbuts
        else:
            buts = [
                UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemAdd, self, SEL(b'onAddBut')).autorelease(),
                UIBarButtonItem.alloc().initWithTitle_style_target_action_(_("Pay to"), UIBarButtonItemStyleDone, self, SEL(b'onPickerPayTo')).autorelease(),
            ]
            self.addBut = buts[0]
            self.doneBut = buts[1]
            self.navigationItem.rightBarButtonItems = buts
        
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()
        
        gui.ElectrumGui.gui.sigContacts.connect(lambda:self.needUpdate(), self.ptr.value)
        

    @objc_method
    def initWithStyle_mode_(self, style : int, mode : int) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        if self:
            self.commonInitWithMode_(mode)
        return self

    @objc_method
    def initWithStyle_(self, style : int) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        if self:
            self.commonInitWithMode_(ModeNormal)
        return self

    @objc_method
    def dealloc(self) -> None:
        gui.ElectrumGui.gui.sigContacts.disconnect(self.ptr.value)
        self.needsRefresh = None
        self.blockRefresh = None
        self.selected = None
        self.mode = None
        self.cancelBut = None
        self.doneBut = None
        self.addBut = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        #nib = UINib.nibWithNibName_bundle_("MAYBE_USE_CUSTOM_XIB_HERE", None)
        #self.tableView.registerNib_forCellReuseIdentifier_(nib, CellIdentifiers[0])
        self.refresh()
        
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        try:
            contacts = _Get()
            return len(contacts) if contacts else 1
        except:
            print("Error, exception retrieving contacts from nspy cache")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        try:
            contacts = _Get()
            identifier = CellIdentifiers[0 if contacts else -1]
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            parent = gui.ElectrumGui.gui
            if cell is None:
                cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            if contacts:
                if self.mode == ModeNormal and cell.imageView.image is None:
                    cell.imageView.image = UIImage.imageNamed_("edit_details.png")
                    if not cell.imageView.gestureRecognizers or not len(cell.imageView.gestureRecognizers):
                        gr = UITapGestureRecognizer.alloc().initWithTarget_action_(self, SEL(b'onTapEdit:')).autorelease()
                        cell.imageView.addGestureRecognizer_(gr)
                        cell.imageView.userInteractionEnabled = True
                cell.imageView.tag = indexPath.row
                c = contacts[indexPath.row]
                cell.textLabel.text = c.name
                cell.detailTextLabel.text = c.address_str
                self.setupAccessoryForCell_atIndex_(cell, indexPath.row)
                    
            else:
                empty_cell(cell,_("No contacts. Use + to add a contact."),True)
        except Exception as e:
            utils.NSLog("exception in Contacts tableView_cellForRowAtIndexPath_: %s",str(e))
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
        tv.deselectRowAtIndexPath_animated_(indexPath,False)
        cell = tv.cellForRowAtIndexPath_(indexPath)

        contacts = _Get()
        if not contacts or not len(contacts): return
    
        self.setIndex_selected_(indexPath.row, not self.isIndexSelected_(indexPath.row))
        wasSel = self.setupAccessoryForCell_atIndex_(cell, indexPath.row) # this sometimes fails if address is frozen and/or we are watching only
        self.setIndex_selected_(indexPath.row, wasSel)

        self.selected = self.updateSelectionButtons()

    @objc_method
    def tableView_editingStyleForRowAtIndexPath_(self, tv, indexPath) -> int:
        contacts = _Get()
        if self.mode == ModePicker or not contacts or not len(contacts):
            return UITableViewCellEditingStyleNone
        return UITableViewCellEditingStyleDelete

    @objc_method
    def tableView_commitEditingStyle_forRowAtIndexPath_(self, tv, editingStyle : int, indexPath) -> None:
        contacts = _Get()
        if not contacts or indexPath.row < 0 or indexPath.row >= len(contacts): return
        if editingStyle == UITableViewCellEditingStyleDelete:
            if delete_contact(contacts[indexPath.row]):
                was = self.blockRefresh
                self.blockRefresh = True
                _Updated()
                contacts = _Get()
                self.needsRefresh = False
                if len(contacts):
                    tv.deleteRowsAtIndexPaths_withRowAnimation_([indexPath],UITableViewRowAnimationFade)
                    self.selected = self.updateSelectionButtons()
                    self.blockRefresh = was
                else:
                    self.blockRefresh = was
                    self.refresh()

    ''' 
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        return 150.0
        #return 44.0
    '''

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
            #print ("CONTACTS REFRESHED")

    @objc_method
    def showRefreshControl(self):
        if self.refreshControl is not None and not self.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            self.refreshControl.beginRefreshing()
            self.tableView.setContentOffset_animated_(CGPointMake(0, self.tableView.contentOffset.y-self.refreshControl.frame.size.height), True)
                                            
    @objc_method
    def onOptions_(self, obj : ObjCInstance) -> None:
        print ("On Options")
        return
        # below form coins.py -- here for reference
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
            utils.NSLog("Exception during contacts.py 'onOptions': %s",str(sys.exc_info()[1]))

    @objc_method
    def isIndexSelected_(self, index : int) -> bool:
        try:
            entry = _Get()[index]
            sels = set(list(self.selected))
            return bool(entry.address_str in sels)
        except:
            import sys
            utils.NSLog("Exception during contacts.py 'isIndexSelected': %s",str(sys.exc_info()[1]))
        return False

    @objc_method
    def setIndex_selected_(self, index : int, b : bool) -> None:
        try:
            entry = _Get()[index]
            sels = set(list(self.selected))
            if not b: sels.discard(entry.address_str)
            else: sels.add(entry.address_str)
            self.selected = list(sels)
        except:
            import sys
            utils.NSLog("Exception during contacts.py 'setIndex_selected_': %s",str(sys.exc_info()[1]))

    @objc_method
    def onPickerCancel(self) -> None:
        print ("picker cancel...")
        self.presentingViewController.dismissViewControllerAnimated_completion_(True, None)
        return
        self.selected = []
        self.refresh()
        
    @objc_method
    def onPickerPayTo(self) -> None:
        #print ("picker done/payto...")
        validSels = list(self.updateSelectionButtons())
        #print("valid selections:",*validSels)
        contacts = _Get()
        addys = []
        for entry in contacts:
            if entry.address_str in validSels:
                addys.append(entry.address_str)
        if addys:
            if self.mode == ModePicker:
                utils.get_callback(self, 'on_pay_to')(addys)
            else:
                pay_to(addys)


    @objc_method
    def showNewEditForm_(self, index : int) -> None:
        vc = NewContactVC.new().autorelease()
        if index > -1:
            contacts = _Get()
            if contacts and index < len(contacts):
                utils.nspy_put_byname(vc, contacts[index], 'edit_contact')

        def onOk(entry : ContactsEntry) -> None:
            #print ("parent onOK called...")
            if entry is not None:
                oldEntry = utils.nspy_get_byname(vc, 'edit_contact')
                if oldEntry:
                    delete_contact(oldEntry, False)
                add_contact(entry)
                _Updated()
        utils.add_callback(vc, 'on_ok', onOk)
        self.presentViewController_animated_completion_(vc, True, None)
        
            
    @objc_method
    def onAddBut(self) -> None:
        #print("on add but...")
        self.showNewEditForm_(-1)

    @objc_method
    def onTapEdit_(self, gr : ObjCInstance) -> None:
        self.showNewEditForm_(int(gr.view.tag))

    @objc_method
    def updateSelectionButtons(self) -> ObjCInstance:
        parent = gui.ElectrumGui.gui
        newSels = set()
        if self.doneBut: self.doneBut.enabled = False
        if parent.wallet:
            sels = set(list(self.selected))
            contacts = _Get()
            for c in contacts:
                if c.address_str in sels:
                    newSels.add(c.address_str)
            if len(newSels) and self.doneBut:
                self.doneBut.enabled = True
        return ns_from_py(list(newSels))
    
    @objc_method
    def setupAccessoryForCell_atIndex_(self, cell, index : int) -> bool:
        parent = gui.ElectrumGui.gui
        no_good = parent.wallet is None or parent.wallet.is_watching_only()
        try:
            entry = _Get()[index]
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

class NewContactVC(NewContactBase):
    
    qr = objc_property()
    qrvc = objc_property()
    topCSOrig = objc_property()
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self:
            self.title = _("New Contact")
            self.modalPresentationStyle = UIModalPresentationOverFullScreen
            self.modalTransitionStyle = UIModalTransitionStyleCrossDissolve
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.qrvc = None
        self.qr = None
        self.topCSOrig = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        print("NewContactVC dealloc")
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        NSBundle.mainBundle.loadNibNamed_owner_options_("NewContact",self,None)

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')

        def onOk(bid : objc_id) -> None:
            #print("On OK...")
            address_str = cleanup_address_remove_colon(self.address.text)
            name = self.name.text
            if not Address.is_valid(address_str):
                gui.ElectrumGui.gui.show_error(_("Invalid Address"))
                return
            if not name:
                gui.ElectrumGui.gui.show_error(_("Name is empty"))
                return                
            def doCB() -> None:
                cb = utils.get_callback(self, 'on_ok')
                if callable(cb):
                    entry = None
                    if name and address_str and Address.is_valid(address_str):
                        address = Address.from_string(address_str)
                        entry = ContactsEntry(name, address, address_str, build_contact_tx_list(address))
                    cb(entry)
                self.autorelease()
            self.retain()
            self.presentingViewController.dismissViewControllerAnimated_completion_(True, doCB)
        def onCancel(bid : objc_id) -> None:
            #print("On Cancel...")
            def doCB() -> None:
                cb = utils.get_callback(self, 'on_cancel')
                if callable(cb): cb()
                self.autorelease()
            self.retain()
            self.presentingViewController.dismissViewControllerAnimated_completion_(True, doCB)
        def onQR(bid : objc_id) -> None:
            #print("On QR...")
            if not QRCodeReader.isAvailable:
                utils.show_alert(self, _("QR Not Avilable"), _("The camera is not available for reading QR codes"))
            else:
                self.qr = QRCodeReader.new().autorelease()
                self.qrvc = QRCodeReaderViewController.readerWithCancelButtonTitle_codeReader_startScanningAtLoad_showSwitchCameraButton_showTorchButton_("Cancel",self.qr,True,True,True)
                self.qrvc.modalPresentationStyle = UIModalPresentationFormSheet
                self.qrvc.delegate = self
                self.presentViewController_animated_completion_(self.qrvc, True, None)
        def onCpy(bid : objc_id) -> None:
            try:
                datum = str(self.name.text) if bid.value == self.cpyNameBut.ptr.value else str(self.address.text)
                UIPasteboard.generalPasteboard.string = datum
                print ("copied to clipboard =", datum)
                utils.show_notification(message=_("Text copied to clipboard"))
            except:
                import sys
                utils.NSLog("Exception during NewContactVC 'onCpy': %s",str(sys.exc_info()[1]))

        
        editContact = utils.nspy_get_byname(self, 'edit_contact')
        if editContact:
            self.address.text = editContact.address_str
            self.name.text = editContact.name
        
        self.okBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onOk)
        self.cancelBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCancel)
        self.qrBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onQR)
        self.cpyNameBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCpy)
        self.cpyAddressBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCpy)

    @objc_method
    def reader_didScanResult_(self, reader, result) -> None:
        utils.NSLog("Reader data = '%s'",str(result))
        result = cleanup_address_remove_colon(result)
        if not Address.is_valid(result):
            title = _("Invalid QR Code")
            message = _("The QR code does not appear to be a valid BCH address.\nPlease try again.")
            reader.stopScanning()
            gui.ElectrumGui.gui.show_error(
                title = title,
                message = message,
                onOk = lambda: reader.startScanning(),
                vc = self.qrvc
            )
        else:
            self.address.text = result
            self.readerDidCancel_(reader)
             
    @objc_method
    def readerDidCancel_(self, reader) -> None:
        if reader is not None: reader.stopScanning()
        self.dismissViewControllerAnimated_completion_(True, None)
        self.qr = None
        self.qrvc = None
        
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.translateUI()
        
    @objc_method
    def translateUI(self) -> None:
        if not self.viewIfLoaded: return
        self.blurb.text = _("Contacts are a convenient feature to associate addresses with user-friendly names. "
                            "Contacts can be accessed when sending a payment via the 'Send' tab.")
        self.addressTit.text = _("Address") + ':'
        self.nameTit.text = _("Name") + ':'
        self.title = _("New Contact")
        self.name.placeholder = _("Name")
        self.address.placeholdeer = _("Address")
        self.okBut.setTitle_forState_(_("OK"), UIControlStateNormal)
        self.cancelBut.setTitle_forState_(_("Cancel"), UIControlStateNormal)

    @objc_method
    def textFieldDidEndEditing_(self, tf : ObjCInstance) -> None:
        if self.topCSOrig is not None:
            self.topCS.constant = self.topCSOrig

    @objc_method
    def textFieldDidBeginEditing_(self, tf : ObjCInstance) -> None:
        if self.topCSOrig is None:
            self.topCSOrig = self.topCS.constant
        if utils.is_landscape():
            self.topCS.constant = 0


class ContactsMgr(utils.DataMgr):
    def doReloadForKey(self, key) -> list:
        # key is ignored
        return get_contacts() or list()

def _Get() -> list:
    return gui.ElectrumGui.gui.contactsMgr.get(None)

def _Updated() -> None:
    gui.ElectrumGui.gui.refresh_components('contacts')

def build_contact_tx_list(address : Address) -> list:
    parent = gui.ElectrumGui.gui
    ret = list()
    if isinstance(address, Address) and parent and parent.historyMgr:
        alltxs = parent.historyMgr.get(None)
        for hentry in alltxs:
            if hentry.tx:
                ins = hentry.tx.inputs()
                for x in ins:
                    xa = x['address']
                    if isinstance(xa, PublicKey):
                        xa = xa.toAddress()
                    if isinstance(xa, Address) and xa.to_storage_string() == address.to_storage_string():
                        ret.append(hentry.tx_hash)
                        break
                outs = hentry.tx.get_outputs()
                for x in outs:
                    xa, dummy = x
                    if isinstance(xa, Address) and xa.to_storage_string() == address.to_storage_string():
                        ret.append(hentry.tx_hash)
                        break
    #print("build_contact_tx_list: address", address.to_ui_string(), "found", len(ret),"associated txs")
    return ret


def get_contacts() -> list:
    ''' Builds a list of
        ContactsEntry tuples:
        
        ContactsEntry = namedtuple("ContactsEntry", "name address address_str tx_hashes")

        '''
    t0 = time.time()
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    if wallet is None:
        utils.NSLog("get_contacts: wallent was None, returning early")
        return None
    c = wallet.contacts
    contacts = list()
    for addr,tupl in c.items():
        typ, name = tupl
        if typ == 'address' and Address.is_valid(addr):
            address = Address.from_string(addr)
            tx_hashes = build_contact_tx_list(address)
            entry = ContactsEntry(name, address, addr, tx_hashes)
            contacts.append(entry)    
    contacts.sort(key=lambda x: [x.name, x.address_str], reverse=False)
    utils.NSLog("get_contacts: fetched %d contacts in %f ms",len(contacts), (time.time()-t0)*1000.0)
    return contacts

def delete_contact(entry : ContactsEntry, do_write = True) -> int:
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    if wallet is None:
        utils.NSLog("delete_contacts: wallent was None, returning early")
        return None
    c = wallet.contacts
    if not c:
        return None
    n = len(c)
    c.pop(entry.address_str)
    n2 = len(c)
    if n2 < n:
        c.save()
        if do_write:
            c.storage.write()
    ret = n - n2
    utils.NSLog("deleted %d contact(s)", ret)
    return ret

def add_contact(entry : ContactsEntry, do_write = True) -> bool:
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    if wallet is None:
        utils.NSLog("add_contact: wallent was None, returning early")
        return False
    c = wallet.contacts
    if c is None:
        utils.NSLog("add_contact: contacts was None, returning early")
        return False
    n = len(c)
    c[entry.address_str] = ("address", entry.name)
    n2 = len(c)
    c.save()
    if do_write:
        c.storage.write()
    ret = n2 - n
    utils.NSLog("added %d contact(s)", ret)
    return bool(ret)

def empty_cell(cell : ObjCInstance, txt : str = "*Error*", italic : bool = False) -> ObjCInstance:
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
    cell.imageView.image = None
    return cell

def cleanup_address_remove_colon(result : str) -> str:
    if result is not None:
        result = str(result).strip()
        
        if ':' in result:
            try:
                result = ''.join(result.split(':')[1:])
            except:
                pass
    return result

def pay_to(addys : list) -> bool:
    print("payto:",*addys)
    if len(addys) > 1:
        gui.ElectrumGui.gui.show_error(title=_("Coming Soon"),
                                       message=_("This version of Electron Cash currently only supports sending to 1 address at a time! Sorry!"))
        return False
    gui.ElectrumGui.gui.jump_to_send_with_pay_to(addys[0])
    return True