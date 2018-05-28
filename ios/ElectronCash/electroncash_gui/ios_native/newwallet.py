from . import utils
from . import gui
from electroncash.i18n import _, language
from typing import Any
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
    def shouldPerformSegueWithIdentifier_sender_(self, identifier, sender) -> bool:
        print("shouldPerformSegueWithIdentifier_sender_(",identifier,",",str(sender),")... TODO: IMPLEMENT!")
        #TODO: check passwords match, wallet name is unique
        return True
    
    @objc_method
    def prepareForSegue_sender_(self, segue, sender) -> None:
        print("prepareForSeque called")
        # TODO: pass along wallet name, password, etc...?
        _SetParam(self, 'WalletName', self.walletName.text)
        _SetParam(self, 'WalletPass', self.walletPw2.text)

        print("params=",_Params(self))


def _Params(vc : UIViewController) -> dict():
    return py_from_ns(vc.navigationController.params)

def _SetParams(vc : UIViewController, params : dict) -> None:
    vc.navigationController.params = params

def _SetParam(vc : UIViewController, paramName : str, paramValue : Any) -> None:
    d = _Params(vc)
    if not paramValue:
        d.pop(paramName, None)
    else:
        d[paramName] = paramValue
    _SetParams(vc, d)