from . import utils
from . import gui
from electroncash.i18n import _, language
from .uikit_bindings import *
from collections import namedtuple
from electroncash import bitcoin

def parent() -> object:
    return gui.ElectrumGui.gui

PrivateKeyEntry = namedtuple("PrivateKeyEntry", "address privkey is_frozen is_change")

class PrivateKeyDialog(UIViewController):
    
    defaultBG = objc_property()
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.title = "Private Key"
        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("PrivateKeyDialog dealloc")
        utils.nspy_pop(self)
        self.title = None
        self.view = None
        self.defaultBG = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("PrivateKeyDialog",None,None)
        v = None
        
        for o in objs:
            if isinstance(o, UIView):
                v = o
        if v is None:
            raise ValueError('PrivateKeyDialog XIB is missing either the primary view !')

   
        entry = utils.nspy_get_byname(self, 'entry')
        
        views = v.allSubviewsRecursively()
        # attach copy/qr button actions
        for view in views:
            if isinstance(view, UIButton):
                if view.tag < 100:
                    continue
                which = view.tag % 100
                if which == 20: # copybut
                    view.addTarget_action_forControlEvents_(self, SEL(b'onCpyBut:'), UIControlEventPrimaryActionTriggered)
                elif which == 30: # qrbut
                    view.addTarget_action_forControlEvents_(self, SEL(b'onQRBut:'), UIControlEventPrimaryActionTriggered)

        self.view = v
                
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.refresh()
        parent().cash_addr_sig.connect(lambda: self.refresh(), self)
        
        
    @objc_method
    def viewWillDisappear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillDisappear:', animated, argtypes=[c_bool])
        parent().cash_addr_sig.disconnect(self)
        
    @objc_method
    def refresh(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        entry = utils.nspy_get_byname(self, 'entry')
 
        lbl = v.viewWithTag_(100)
        lbl.text = _("Address") + ":"        
        lbl = v.viewWithTag_(110)
        lbl.text = str(entry.address)
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
        lbl.text = _("Script type") + ":"
        lbl = v.viewWithTag_(210)
        xtype = bitcoin.deserialize_privkey(entry.privkey)[0]
        lbl.text = xtype

        lbl = v.viewWithTag_(300)
        lbl.text = _("Private key") + ":"
        tv = v.viewWithTag_(310)
        tv.text = str(entry.privkey)
        
        lbl = v.viewWithTag_(400)
        lbl.text = _("Redeem Script") + ":"
        tv = v.viewWithTag_(410)
        tv.text = entry.address.to_script().hex()
        
        
    @objc_method
    def onCpyBut_(self, sender) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        data = ""
        if sender.tag == 120: data = str(entry.address)
        elif sender.tag == 320: data = str(entry.privkey)
        elif sender.tag == 420: data = entry.address.to_script().hex()
        UIPasteboard.generalPasteboard.string = data
        utils.show_notification(message=_("Text copied to clipboard"))

    @objc_method
    def onQRBut_(self, sender) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        data = ""
        if sender.tag == 130: data = str(entry.address)
        elif sender.tag == 330: data = str(entry.privkey)
        elif sender.tag == 430: data = entry.address.to_script().hex()
        qrvc = utils.present_qrcode_vc_for_data(vc=self,
                                                data=data,
                                                title = _('QR code'))
        parent().add_navigation_bar_close_to_modal_vc(qrvc)
        

