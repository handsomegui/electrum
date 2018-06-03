#
# This file is:
#     Copyright (C) 2018 Calin Culianu <calin.culianu@gmail.com>
#
# MIT License

from . import utils
from . import gui
from electroncash.i18n import _, language
from electroncash.address import Address

from .uikit_bindings import *
from .custom_objc import *


class AddrConvVC(AddrConvBase):
   
    qr = objc_property()
    qrvc = objc_property()
   
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self:
            self.qr = None
            self.qrvc = None
            self.title = _("Address Converter")
            self.tabBarItem.image = UIImage.imageNamed_("tab_converter.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.qr = None
        self.qrvc = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        NSBundle.mainBundle.loadNibNamed_owner_options_("AddressConverter",self,None)
        
    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        self.address.text = ""
        self.doConversion_("")  # disables copy buttons
        
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        
        txt = _(
            "This tool helps convert between address formats for Bitcoin "
            "Cash addresses.\nYou are encouraged to use the 'Cash address' "
            "format."
            )
        
        self.blurb.text = txt.replace('\n','\n\n')
        
        self.address.placeholder = _('Address to convert')
        self.cashTit = _('Cash address')
        self.legacyTit = _('Legacy address')
        
    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        #print("tf should return")
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def onBut_(self, but) -> None:
        if but.ptr == self.cpyCashBut.ptr:
            gui.ElectrumGui.gui.copy_to_clipboard(self.cash.text, 'Address')
        elif but.ptr == self.cpyLegBut.ptr:
            gui.ElectrumGui.gui.copy_to_clipboard(self.legacy.text, 'Address')
        elif but.ptr == self.qrBut.ptr:
            if not QRCodeReader.isAvailable:
                utils.show_alert(self, _("QR Not Avilable"), _("The camera is not available for reading QR codes"))
            else:
                self.qr = QRCodeReader.new().autorelease()
                self.qrvc = QRCodeReaderViewController.readerWithCancelButtonTitle_codeReader_startScanningAtLoad_showSwitchCameraButton_showTorchButton_("Cancel",self.qr,True,True,True)
                self.qrvc.modalPresentationStyle = UIModalPresentationFormSheet
                self.qrvc.delegate = self
                self.presentViewController_animated_completion_(self.qrvc, True, None)

    @objc_method
    def reader_didScanResult_(self, reader, result) -> None:
        utils.NSLog("Reader data = '%s'",str(result))
        result = str(result).strip()
        
        if not self.doConversion_(result):
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
    def onAddress_(self, tf) -> None:
        print("onAddress:",tf.text)
        self.doConversion_(tf.text)
        
    @objc_method
    def doConversion_(self, text) -> bool:
        self.cash.text = ""
        self.legacy.text = ""
        self.cpyCashBut.enabled = False
        self.cpyLegBut.enabled = False
        text = text.strip()
        
        addy = None
        
        try:
            addy = Address.from_string(text)
        except:
            pass

        if addy:
            self.cash.text = addy.to_full_string(Address.FMT_CASHADDR)
            self.legacy.text = addy.to_full_string(Address.FMT_LEGACY)
            self.cpyCashBut.enabled = True
            self.cpyLegBut.enabled = True
            return True
        return False
