#!/usr/bin/env python3
#
# Electron Cash - lightweight Bitcoin Cash client
# Copyright (C) 2012 thomasv@gitorious
# Copyright (C) 2018 calin.culianu@gmail.com
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import math
import re
from typing import Callable, Any
from .uikit_bindings import *
from . import utils
from .custom_objc import *

from electroncash.i18n import _
from electroncash import WalletStorage, Wallet
       

def Create_SeedDisplayVC(seed, passphrase) -> ObjCInstance:
    ret = SeedDisplayVC.seedDisplayVCWithSeed_passphrase_(seed, passphrase)
    #utils.add_callback(ret, 'okcallback', callback)
    return ret

class SeedDisplayVC(UIViewController):
    okBut = objc_property()
    seedLbl = objc_property()
    titLbl = objc_property()
    msgLbl = objc_property()
    seed = objc_property()
    passphrase = objc_property()
    
    @objc_classmethod
    def seedDisplayVCWithSeed_passphrase_(cls : ObjCInstance, seed : ObjCInstance, passphrase : ObjCInstance) -> ObjCInstance:
        ret = SeedDisplayVC.new().autorelease()
        ret.seed = seed
        ret.passphrase = passphrase
        ret.modalPresentationStyle = UIModalPresentationOverFullScreen#UIModalPresentationOverCurrentContext
        ret.modalTransitionStyle = UIModalTransitionStyleCrossDissolve
        ret.disablesAutomaticKeyboardDismissal = False
        return ret
    
    @objc_method
    def dealloc(self) -> None:
        self.okBut = None
        self.seedLbl = None
        self.titLbl = None
        self.msgLbl = None
        self.seed = None
        self.passphrase = None
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')    
    
    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        pass
    
    @objc_method
    def loadView(self) -> None:
        seed = self.seed
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("SeedDialog",None,None)
        v = None
        for o in objs:
            if isinstance(o, UIView):
                v = o
            elif isinstance(o, UITapGestureRecognizer):
                o.addTarget_action_(self, SEL('onSeedLblTap:'))
        allviews = v.allSubviewsRecursively()
        for a in allviews:
            if isinstance(a, UILabel):
                # translate UI automatically since placeholder text has potential translations 
                a.text = _(a.text)
            elif isinstance(a, UIButton):
                a.setTitle_forState_(_(a.titleForState_(UIControlStateNormal)), UIControlStateNormal)
        self.titLbl = v.viewWithTag_(20)
        self.okBut = v.viewWithTag_(1000)
        self.msgLbl = v.viewWithTag_(200)
        self.seedLbl = v.viewWithTag_(100)
        
        self.titLbl.text = _("Your wallet generation seed is:")
        self.msgLbl.attributedText = utils.nsattributedstring_from_html(seed_warning_msg(py_from_ns(self.seed),py_from_ns(self.passphrase)))
        utils.uilabel_replace_attributed_text(self.seedLbl, py_from_ns(self.seed))
        sv = UIScrollView.alloc().initWithFrame_(CGRectMake(0,0,320,350)).autorelease()
        sv.contentSize = CGSizeMake(320,400)
        sv.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(0.,0.,0.,0.3)
        sv.opaque = False
        sv.addSubview_(v)
        self.view = sv

        def onOk(but_in : objc_id) -> None:
            but = ObjCInstance(but_in)
            self.dismissViewControllerAnimated_completion_(True,None)
        self.okBut.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered,onOk)

    @objc_method
    def onCopyBut_(self, but) -> None:
        data = self.seed
        if self.passphrase: data += " / " + self.passphrase
        UIPasteboard.generalPasteboard.string = data
        utils.show_notification(message=_("Text copied to clipboard"))

    @objc_method
    def onQRBut_(self, but) -> None:
        data = self.seed
        if self.passphrase: data += " / " + self.passphrase
        qrvc = utils.present_qrcode_vc_for_data(vc=self,
                                                data=data,
                                                title = _('Wallet Seed'))

        closeButton = UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemStop, self, SEL(b'onModalClose:')).autorelease()
        qrvc.navigationItem.rightBarButtonItem = closeButton
    
    @objc_method
    def onModalClose_(self, but : ObjCInstance) -> None:
        self.dismissViewControllerAnimated_completion_(True, None)

    @objc_method
    def onSeedLblTap_(self, uigr : ObjCInstance) -> None:
        utils.show_alert(
            vc = self,
            title = _("Options"),
            message = _("Wallet Seed"),
            actions = [
                [ _('Cancel') ],
                [ _('Copy to clipboard'), self.onCopyBut_, None ],
                [ _('Show as QR code'), self.onQRBut_, None ],
            ],
            cancel = _('Cancel'),
            style = UIAlertControllerStyleActionSheet
        )

def seed_warning_msg(seed, passphrase):
    return ''.join([
        '<font face="Arial, Helvetica">',
        "<p>",
        str(_("Your seed extension is") + ": <b>" + passphrase + "</b></p><p>") if passphrase else '',
        _("Please save these %d words on paper (order is important). "),
        _("This seed will allow you to recover your wallet in case "
          "of computer failure."),
        "</p>",
        '<p>',
        "<b>" + _("WARNING") + ":</b>",
        "<ul>",
        "<li>" + _("Never disclose your seed.") + "</li>",
        "<li>" + _("Never type it on a website.") + "</li>",
        "<li>" + _("Do not store it electronically.") + "</li>",
        "</ul>",
        '</p>',
        '</font>',
    ]) % len(seed.split())
