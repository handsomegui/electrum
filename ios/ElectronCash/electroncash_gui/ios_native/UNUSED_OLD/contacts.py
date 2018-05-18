''' This is just the old-style "NewContacts" UI.  The corresponding .XIB is in Resources/UNUSED_OLD/OLD_NewContact.xib '''

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
            self.blurb.font = UIFont.systemFontOfSize_weight_(20.0, UIFontWeightSemibold)
        
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
        isnew = not utils.nspy_get_byname(self, 'edit_contact')
        self.title = _("New Contact") if isnew else _("Edit Contact")
        self.blurb.text = _("Contacts are a convenient feature to associate addresses with user-friendly names. "
                            "Contacts can be accessed when sending a payment via the 'Send' tab.") if isnew else self.title
        self.addressTit.text = _("Address") + ':'
        self.nameTit.text = _("Name") + ':'
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
