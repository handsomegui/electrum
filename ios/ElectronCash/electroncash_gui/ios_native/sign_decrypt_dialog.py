#
# This file is:
#     Copyright (C) 2018 Calin Culianu <calin.culianu@gmail.com>
#
# MIT License
#
from .uikit_bindings import *
from . import utils
from . import gui
from . import addresses
from electroncash.i18n import _, language
from electroncash import bitcoin
from electroncash.address import Address
import sys, traceback, base64
from collections import namedtuple

def parent() -> object:
    return gui.ElectrumGui.gui

DialogData = namedtuple("DialogData", "address pubkey")

SignVerify = 0
EncryptDecrypt = 1

class SignDecryptVC(UIViewController):
    
    mode = objc_property()
    
    @objc_method
    def initWithMode_(self, mode : int) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if mode not in (SignVerify, EncryptDecrypt):
            utils.NSLog(" *** ERROR -- mode %d passed to SignDecryptVC.initWithMode is not valid! Defaulting to mode 'SignVerify'",mode)
            mode = 0
        self.title = _("Sign/verify Message") if mode == SignVerify else _("Encrypt/decrypt Message")
        self.mode = mode
        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("PrivateKeyDialog dealloc")
        utils.nspy_pop(self)
        self.title = None
        self.view = None
        self.mode = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("SignVerify",None,None)
        v = None
        
        for o in objs:
            if isinstance(o, UIView):
                v = o
        if v is None:
            raise ValueError('SignVerify XIB is missing either the primary view !')

   
        data = utils.nspy_get_byname(self, 'data')
        
        views = v.allSubviewsRecursively()
        # attach copy/qr button actions
        for view in views:
            if isinstance(view, UIButton):
                if view.tag in (220,320):
                    view.addTarget_action_forControlEvents_(self, SEL(b'onCpyBut:'), UIControlEventPrimaryActionTriggered)
                elif view.tag in (120,): # pick address
                    view.addTarget_action_forControlEvents_(self, SEL(b'onPickAddress:'), UIControlEventPrimaryActionTriggered)
                elif view.tag in (1000,2000): #
                    view.addTarget_action_forControlEvents_(self, SEL(b'onExecuteBut:'), UIControlEventPrimaryActionTriggered)
            elif isinstance(view, (UITextField,UITextView)):
                if view.tag in (110,210,310): # address text field
                    spacer = UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemFlexibleSpace, None, None).autorelease()
                    item = UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemDone, self, SEL(b'onCloseKeyboard:')).autorelease()
                    item.tag = view.tag
                    toolBar = UIToolbar.alloc().init().autorelease()
                    toolBar.sizeToFit()
                    toolBar.items = [spacer, item]
                    view.inputAccessoryView = toolBar

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
        data = utils.nspy_get_byname(self, 'data')
        if not data: data = DialogData(None,None)
        text = self.view.viewWithTag_(110).text.strip()
        if self.mode == SignVerify:
            try:
                address = Address.from_string(text)
                data = utils.set_namedtuple_field(data, 'address', address)
            except:
                pass
        elif self.mode == EncryptDecrypt:
            data = utils.set_namedtuple_field(data, 'pubkey', text)
        utils.nspy_put_byname(self, data, 'data')
        
    @objc_method
    def refresh(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        data = utils.nspy_get_byname(self, 'data')
        
        strings = [
            [
                "Message",
                "Address",
                "Signature",
                "Sign",
                "Verify",
            ],
            [
                "Message",
                "Public key",
                "Encrypted",
                "Encrypt",
                "Decrypt",
            ],
        ]
 
        mode = self.mode
        lbl = v.viewWithTag_(100)
        lbl.text = _(strings[mode][1]) + ":"        
        tf = v.viewWithTag_(110)
        if data.pubkey and not isinstance(data.pubkey, str):
            data = utils.set_namedtuple_field(data, 'pubkey', data.pubkey.to_ui_string())
            utils.nspy_put_byname(self,data,'data')
        tf.text = str(data.address.to_ui_string() if data.address else "") if mode == SignVerify else (str(data.pubkey) if data.pubkey else "")
        tf.placeholder = _("Enter or pick address") if mode == SignVerify else _("Choose address or enter a public key")

        lbl = v.viewWithTag_(200)
        lbl.text = _(strings[mode][0]) + ":"
        tv = v.viewWithTag_(210)

        lbl = v.viewWithTag_(300)
        lbl.text = _(strings[mode][2]) + ":"
        tv = v.viewWithTag_(310)
        tv.delegate = self
        
        but = v.viewWithTag_(1000)
        but.setTitle_forState_(_(strings[mode][3]),UIControlStateNormal)
        but = v.viewWithTag_(2000)
        but.setTitle_forState_(_(strings[mode][4]),UIControlStateNormal)
        
    @objc_method
    def onCpyBut_(self, sender : ObjCInstance) -> None:
        if sender.tag in (220,320):
            data = self.view.viewWithTag_(sender.tag-10).text
            if data:
                parent().copy_to_clipboard(data)

        
    @objc_method
    def onPickAddress_(self, sender : ObjCInstance) -> None:
        def pickedAddress(entry) -> None:
            data = utils.nspy_get_byname(self, 'data')
            pubkey = None
            try:
                pubkey =  parent().wallet.get_public_key(entry.address)
            except:
                pass
            if pubkey is not None and not isinstance(pubkey,str):
                pubkey = pubkey.to_ui_string()
            data = DialogData(entry.address, pubkey)
            utils.nspy_put_byname(self, data, 'data')
            # refresh will be auto-called as a result of viewWillAppear
        addresses.present_modal_address_picker(pickedAddress, self)

    @objc_method
    def onCloseKeyboard_(self, sender : ObjCInstance) -> None:
        self.view.viewWithTag_(sender.tag).resignFirstResponder()
        
    @objc_method
    def textViewDidBeginEditing_(self, tv : ObjCInstance) -> None:
        sv = self.view
        if isinstance(sv, UIScrollView) and utils.is_iphone(): # fee manual edit, make sure it's visible
            # try and center the text fields on the screen.. this is an ugly HACK.
            # todo: fixme!
            frame = tv.frame
            frame.origin.y += 150 + 64
            sv.scrollRectToVisible_animated_(frame, True)

    @objc_method
    def onExecuteBut_(self, sender : ObjCInstance) -> None:
        if sender.tag == 1000:  # sign/encrypt
            if self.mode == SignVerify:
                self.doSign()
            else:
                self.doEncrypt()
        elif sender.tag == 2000: # verify/decrypt
            if self.mode == SignVerify:
                self.doVerify()
            else:
                self.doDecrypt()

    @objc_method
    def doSign(self) -> None:
        addrtf = self.view.viewWithTag_(110)
        address = str(addrtf.text).strip()
        messagetv = self.view.viewWithTag_(210)
        message = str(messagetv.text).strip()
        signaturetv = self.view.viewWithTag_(310)
        try:
            print ("address = ", address)
            addr = Address.from_string(address)
        except:
            parent().show_error(_('Invalid Bitcoin Cash address.'))
            return
        if addr.kind != addr.ADDR_P2PKH:
            msg_sign = _("Signing with an address actually means signing with the corresponding "
                        "private key, and verifying with the corresponding public key. The "
                        "address you have entered does not have a unique public key, so these "
                        "operations cannot be performed.") + '\n\n' + \
                       _('The operation is undefined. Not just in Electrum, but in general.')
            parent().show_message(_('Cannot sign messages with this type of address.') + '\n\n' + msg_sign)
        if not parent().wallet:
            return
        if parent().wallet.is_watching_only():
            parent().show_message(_('This is a watching-only wallet.'))
            return
        if not parent().wallet.is_mine(addr):
            parent().show_message(_('Address not in wallet.'))
            return
        
        def onPw(password : str) -> None:
            try:
                signed = parent().wallet.sign_message(addr, message, password)
            except:
                parent().show_error(str(sys.exc_info()[1]))
                return
            signaturetv.text = base64.b64encode(signed).decode('ascii')
            parent().show_message(_("The signature for the provided message has been pasted into the signature text box."),title=_("Success"))

        parent().prompt_password_if_needed_asynch(onPw)
    
    @objc_method
    def doVerify(self) -> None:
        addrtf = self.view.viewWithTag_(110)
        address_str = str(addrtf.text).strip()
        messagetv = self.view.viewWithTag_(210)
        message = str(messagetv.text).strip()
        signaturetv = self.view.viewWithTag_(310)
        signature = str(signaturetv.text).strip()
        
        if not signature:
            parent().show_message(_("Please provide both a signature and a message to verify"))
            return
        
        try:
            address = Address.from_string(address_str)
        except:
            parent().show_error(_('Invalid Bitcoin Cash address.'))
            return
        message = message.encode('utf-8')
        try:
            # This can throw on invalid base64
            sig = base64.b64decode(signature)
        except:
            verified = False
        else:
            verified = bitcoin.verify_message(address, sig, message)

        if verified:
            parent().show_message(_("Signature verified"), title=_("Success"))
        else:
            parent().show_error(_("Wrong signature"))
    
    @objc_method
    def doEncrypt(self) -> None:
        message = self.view.viewWithTag_(210).text
        message = message.encode('utf-8')
        pubkey = self.view.viewWithTag_(110).text.strip()
        encryptedTV = self.view.viewWithTag_(310)
        
        if not pubkey:
            parent().show_message(_("Please provide a public key or select an address"))
            return
        
        try:
            encrypted = bitcoin.encrypt_message(message, pubkey)
            encryptedTV.text = str(encrypted.decode('ascii'))
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            self.show_error(str(e))

    
    @objc_method
    def doDecrypt(self) -> None:
        if not parent().wallet: return
        if parent().wallet.is_watching_only():
            self.show_message(_('This is a watching-only wallet.'))
            return
        
        cyphertext = self.view.viewWithTag_(310).text
        pubkey = self.view.viewWithTag_(110).text.strip()
        
        if not pubkey or not cyphertext:
            parent().show_message(_("Please provide a public key and cyphertext to decrypt"))
            return            
        
        def onPw(password: str) -> None:
            try:
                plaintext = parent().wallet.decrypt_message(pubkey, cyphertext, password)
                if plaintext is None:
                    raise BaseException('Unspecified failure in decoding cyphertext')
                plaintext = plaintext.decode('utf-8')
            except BaseException as e:
                err = str(e)
                if "Incorrect password" in err:
                    err = _("The specified public key cannot decrypt this cyphertext.\nPlease specify the correct key to decrypt.")
                parent().show_error(err)
                return
            self.view.viewWithTag_(210).text = plaintext
            parent().show_message(_("The message has been successfully decrypted"), title=_("Success"))
        parent().prompt_password_if_needed_asynch(onPw) 

def Create_SignVerify_VC(address, pubkey = None) -> ObjCInstance:
    vc = SignDecryptVC.alloc()
    utils.nspy_put_byname(vc, DialogData(address, pubkey), 'data')
    vc.initWithMode_(SignVerify).autorelease()
    return vc

def Create_EncryptDecrypt_VC(address, pubkey) -> ObjCInstance:
    vc = SignDecryptVC.alloc()
    utils.nspy_put_byname(vc, DialogData(address, pubkey), 'data')
    vc.initWithMode_(EncryptDecrypt).autorelease()
    return vc
