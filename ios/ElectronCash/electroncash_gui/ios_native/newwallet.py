from . import utils
from . import gui
from electroncash.i18n import _, language
from electroncash.mnemonic import Mnemonic
from typing import Any
from .uikit_bindings import *
from .custom_objc import *


class NewWalletVC(NewWalletVCBase):
    origPlaceholders = objc_property()
    origLabelTxts = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here
        self.origPlaceholders = None
        self.origLabelTxts = None
        send_super(__class__, self, 'dealloc')


    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        
    @objc_method
    def translateUI(self) -> None:
        lbls = [ self.walletNameTit, self.walletPw1Tit, self.walletPw2Tit ]
        if not self.origLabelTxts:
            self.origLabelTxts = { lbl.ptr.value : lbl.text for lbl in lbls }
        d = self.origLabelTxts
        for lbl in lbls:
            lbl.setText_withKerning_(_(d[lbl.ptr.value]), utils._kern)
                
        tfs = [ self.walletName, self.walletPw1, self.walletPw2 ]
        if not self.origPlaceholders:
            self.origPlaceholders = { tf.ptr.value : tf.placeholder for tf in tfs }
        d = self.origPlaceholders
        for tf in tfs:
            tf.placeholder = _(d[tf.ptr.value])
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
        if tf.ptr == self.walletName.ptr:
            tf.text = utils.pathsafeify(tf.text)
        utils.uitf_redo_attrs(tf)

    @objc_method
    def textFieldDidBeginEditing_(self, tf : ObjCInstance) -> None:
        pass
    
    
    @objc_method
    def doChkFormOk(self) -> bool:
        self.walletName.text = utils.pathsafeify(self.walletName.text)
        errMsg = ''
        if not self.walletName.text:
            errMsg = _("Wallet name is empty. Please enter a wallet name to proceed.")
        elif gui.ElectrumGui.gui.check_wallet_exists(self.walletName.text):
            errMsg = _("A wallet with that name already exist. Please enter a different wallet name to proceed.")
        elif not self.walletPw1.text:
            errMsg = _("Wallet password is empty. Please set a wallet password to proceed. You can disable wallet password protection later if you wish.")
        elif self.walletPw1.text != self.walletPw2.text:
            errMsg = _("Wallet passwords do not match. Please confirm the password you wish to set for your wallet by entering the same password twice.")

        if errMsg:
            utils.uilabel_replace_attributed_text(self.errMsg, errMsg, font = UIFont.italicSystemFontOfSize_(14.0))
        self.errMsgView.setHidden_(not errMsg)
        return not errMsg

    @objc_method
    def shouldPerformSegueWithIdentifier_sender_(self, identifier, sender) -> bool:
        # check passwords match, wallet name is unique
        return self.doChkFormOk()
        
    
    @objc_method
    def prepareForSegue_sender_(self, segue, sender) -> None:
        # pass along wallet name, password, etc..
        _SetParam(self, 'WalletName', self.walletName.text)
        _SetParam(self, 'WalletPass', self.walletPw2.text)

class NewWalletSeed1(NewWalletSeed1Base):
    origLabelTxts = objc_property()
    seed = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here
        self.origLabelTxts = None
        self.seed = None
        send_super(__class__, self, 'dealloc')

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        utils.uilabel_replace_attributed_text(self.seedtv, " ", font = UIFont.systemFontOfSize_weight_(16.0, UIFontWeightBold))
        
    @objc_method
    def translateUI(self) -> None:
        lbls = [ self.seedTit, self.info ]
        if not self.origLabelTxts:
            self.origLabelTxts = { lbl.ptr.value : lbl.text for lbl in lbls }
        d = self.origLabelTxts
        for lbl in lbls:
            if lbl.ptr == self.info.ptr:
                utils.uilabel_replace_attributed_text(lbl, _(d[lbl.ptr.value]), font=UIFont.italicSystemFontOfSize_(14.0))
            else:
                lbl.setText_withKerning_(_(d[lbl.ptr.value]), utils._kern)
   
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.translateUI()
        self.infoView.setHidden_(True)

    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewDidAppear:', animated, argtypes=[c_bool])
        if not self.seed:
            self.infoView.setHidden_(True)
            def GenSeed() -> str:
                return _Mnem().make_seed()
            def OnSuccess(result : str) -> None:
                self.infoView.setHidden_(False)
                self.seed = result
                utils.uilabel_replace_attributed_text(self.seedtv, self.seed)        
            utils.WaitingDialog(self, _("Generating seed..."), GenSeed,  OnSuccess)
        else:
            self.infoView.setHidden_(False)
            utils.uilabel_replace_attributed_text(self.seedtv, self.seed)
    
    @objc_method
    def shouldPerformSegueWithIdentifier_sender_(self, identifier, sender) -> bool:
        return bool(self.seed)
        
    
    @objc_method
    def prepareForSegue_sender_(self, segue, sender) -> None:
        # pass along wallet seed
        s = py_from_ns(self.seed)
        sl = py_from_ns(self.seed).split()
        _SetParam(self, 'seed', s)
        _SetParam(self, 'seed_list', sl)
        if isinstance(segue.destinationViewController, NewWalletSeed2):
            segue.destinationViewController.seed = s
            segue.destinationViewController.seedList = sl
        #print("params=",_Params(self))

class NewWalletSeed2(NewWalletSeed1Base):
    origLabelTxts = objc_property()
    seed = objc_property()
    seedList = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here
        self.origLabelTxts = None
        self.seed = None
        self.seedList = None
        send_super(__class__, self, 'dealloc')

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        utils.uilabel_replace_attributed_text(self.seedtv, " ", font = UIFont.systemFontOfSize_weight_(16.0, UIFontWeightBold))
        self.seedtv.text = '' # now clear it again..
        if not self.kvc:
            vcs = self.childViewControllers
            for vc in vcs:
                if isinstance(vc, KeyboardVC):
                    self.kvc = vc
        if self.kvc:
            self.kvc.textInput = self.seedtv
        else:
            utils.NSLog("ERROR: NewWalletSeed2 cannot find the KeyboardVC! FIXME!")
        
    @objc_method
    def translateUI(self) -> None:
        lbls = [ self.seedTit, self.info ]
        if not self.origLabelTxts:
            self.origLabelTxts = { lbl.ptr.value : lbl.text for lbl in lbls }
        d = self.origLabelTxts
        for lbl in lbls:
            if lbl.ptr == self.info.ptr:
                utils.uilabel_replace_attributed_text(lbl, _(d[lbl.ptr.value]), font=UIFont.italicSystemFontOfSize_(14.0))
            else:
                lbl.setText_withKerning_(_(d[lbl.ptr.value]), utils._kern)
   
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.translateUI()
 
    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewDidAppear:', animated, argtypes=[c_bool])
        #print("got seed list",*self.seedList)
        self.seedtv.becomeFirstResponder()
    
    @objc_method
    def shouldPerformSegueWithIdentifier_sender_(self, identifier, sender) -> bool:
        return bool(self.seed)
        
    
    @objc_method
    def prepareForSegue_sender_(self, segue, sender) -> None:
        # TODO: stuff
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

_mnem = None   
def _Mnem() -> None:
    global _mnem
    if not _mnem: _mnem = Mnemonic()
    return _mnem