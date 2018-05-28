from . import utils
from . import gui
from electroncash.i18n import _, language

from .uikit_bindings import *
from .custom_objc import *


class NewWalletVC(NewWalletVCBase):
    origPlaceholders = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here
        self.origPlaceholders = None
        send_super(__class__, self, 'dealloc')


    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        
    @objc_method
    def translateUI(self) -> None:
        self.walletNameTit.setText_withKerning_(_("Wallet Name"), utils._kern)
        self.walletPw1Tit.setText_withKerning_(_("Wallet Password"), utils._kern)
        self.walletPw2Tit.setText_withKerning_(_("Confirm Wallet Password"), utils._kern)
        
        tfs = [ self.walletName, self.walletPw1, self.walletPw2 ]
        if not self.origPlaceholders:
            self.origPlaceholders = { tf.ptr.value : tf.placeholder for tf in tfs }
        for tf in tfs:
            tf.placeholder = _(self.origPlaceholders[tf.ptr.value])
            utils.uitf_redo_attrs(tf)
    
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.translateUI()
    
    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidEndEditing_(self, tf : ObjCInstance) -> None:
        utils.uitf_redo_attrs(tf)

    @objc_method
    def textFieldDidBeginEditing_(self, tf : ObjCInstance) -> None:
        pass
    
    @objc_method
    def onNext(self) -> None:
        print ("NEXT  TODO: implement")
