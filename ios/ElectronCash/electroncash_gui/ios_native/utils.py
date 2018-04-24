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
import sys
import os
from inspect import signature
from typing import Callable, Any
from .uikit_bindings import *
from .custom_objc import *

import qrcode
import qrcode.image.svg
import tempfile
import random
import queue
from collections import namedtuple
import threading
import time

from electroncash.i18n import _


bundle_identifier = NSBundle.mainBundle.bundleIdentifier
bundle_domain = '.'.join(bundle_identifier.split('.')[0:-1])
bundle_short_name = bundle_domain + ".ElectronCash"

font_monospace_17 = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular).retain()
font_monospace_17_semibold = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightSemibold).retain()
font_monospace_17_bold = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightBold).retain()

def is_2x_screen() -> bool:
    return True if UIScreen.mainScreen.scale > 1.0 else False

def is_iphone() -> bool:
    return bool(UI_USER_INTERFACE_IDIOM() == UIUserInterfaceIdiomPhone)

def is_ipad() -> bool:
    return not is_iphone()

def get_fn_and_ext(fileName: str) -> tuple:
    *p1, ext = fileName.split('.')
    fn=''
    if len(p1) is 0:
        fn = ext
        ext = None
    else:
        fn = '.'.join(p1) 
    return (fn,ext)

def get_user_dir():
    dfm = NSFileManager.defaultManager
    # documents dir
    thedir = dfm.URLsForDirectory_inDomains_(9, 1).objectAtIndex_(0)
    return str(thedir.path)

def get_tmp_dir():
    return str(ObjCInstance(uikit.NSTemporaryDirectory()))

def uiview_set_enabled(view : ObjCInstance, b : bool) -> None:
    if view is None: return
    view.userInteractionEnabled = bool(b)
    view.alpha = float(1.0 if bool(b) else 0.3)
    view.setNeedsDisplay()
    
def uicolor_custom(name : str) -> ObjCInstance:
    name = name.strip().lower() if name else ""
    if name in ['blue', 'myblue', 'tf', 'password']:
        return UIColor.colorWithRed_green_blue_alpha_(0.91746425629999995, 0.95870447160000005, 0.99979293349999998, 1.0)
    if name in ['change', 'changeaddress', 'change address']:
        return UIColor.colorWithRed_green_blue_alpha_(1.0,0.9,0.3,0.3)
    if name in ['frozen', 'frozenaddress', 'frozen address']:
        return UIColor.colorWithRed_green_blue_alpha_(0.0,0.5,0.5,0.125)
    if name in ['frozentext', 'frozen text', 'frozenaddresstext', 'frozen address text']:
        return UIColor.colorWithRed_green_blue_alpha_(0.0,0.5,0.5,1.0)
    NSLog("uicolor_custom: UNKNOWN custom color '%s' -- returning GRAY -- FIXME"%(str(name)))
    return UIColor.grayColor

# NB: This isn't normally called since you need to specify the full pathname of the resource you want, instead
#     if you need images, call uiimage_get, etc.  This does NOT search recursively, since NSBundle sucks.
def get_bundle_resource_path(fileName: str, directory: str = None) -> str:
    fn,ext = get_fn_and_ext(fileName)
    if directory is None:
        return NSBundle.mainBundle.pathForResource_ofType_(fn, ext)
    return NSBundle.mainBundle.pathForResource_ofType_inDirectory_(fn, ext, directory)

def nsattributedstring_from_html(html : str) -> ObjCInstance:
    data = ns_from_py(html.encode('utf-8'))
    return NSMutableAttributedString.alloc().initWithHTML_documentAttributes_(data,None).autorelease()

def uilabel_replace_attributed_text(lbl : ObjCInstance, text : str, template : ObjCInstance = None) -> ObjCInstance:
    if not isinstance(template, NSAttributedString):
        template = lbl.attributedText
    if template is None:
        template = NSAttrubutedString.new().autorelease()
    astr = NSMutableAttributedString.alloc().initWithAttributedString_(template).autorelease()
    astr.replaceCharactersInRange_withString_(NSRange(0,astr.length()), text)
    lbl.attributedText = astr
    return lbl

###################################################
### Show Share ActionSheet
###################################################
def show_share_actions(vc : ObjCInstance,
                       fileName : str = None,
                       text : str = None,
                       excludedActivityTypes = None,
                       completion: Callable[[],None] = None, # optional completion function that gets called when alert is presented
                       ipadAnchor : object = None,
                       animated : bool = True) -> ObjCInstance:
    items = []
    if fileName:
        items.append(NSURL.fileURLWithPath_(fileName))
    if text is not None:
        items.append(ns_from_py(text))
    avc = UIActivityViewController.alloc().initWithActivityItems_applicationActivities_(items, None).autorelease()
    if excludedActivityTypes is None:
        excludedActivityTypes = [
            UIActivityTypePostToFacebook,
            UIActivityTypePostToTwitter,
            UIActivityTypePostToWeibo,
            UIActivityTypeAssignToContact,
            UIActivityTypeSaveToCameraRoll,
            UIActivityTypeAddToReadingList,
            UIActivityTypePostToFlickr,
            UIActivityTypePostToVimeo,
            UIActivityTypePostToTencentWeibo,
            UIActivityTypeOpenInIBooks,
        ]
    avc.excludedActivityTypes = excludedActivityTypes
    if is_ipad():
        popover = avc.popoverPresentationController()
        if isinstance(ipadAnchor, UIBarButtonItem):
            popover.barButtonItem = ipadAnchor
        else:
            popover.sourceView = vc.view
            if isinstance(ipadAnchor, CGRect):
                rect = ipadAnchor
            else:
                rect = vc.view.frame
                rect = CGRectMake(rect.size.width/2.0,rect.size.height/4.0,0.0,0.0)
            popover.sourceRect = rect
    def onCompletion() -> None:
        if completion is not None:
            #print("Calling completion callback..")
            completion()
    vc.presentViewController_animated_completion_(avc,animated,onCompletion)
    
###################################################
### Show modal alert
###################################################
def show_alert(vc : ObjCInstance, # the viewcontroller to present the alert view in
               title : str, # the alert title
               message : str, # the alert message
               # actions is a list of lists: each element has:  Button names, plus optional callback spec
               # each element of list is [ 'ActionTitle', callable, arg1, arg2... ] for optional callbacks
               actions: list = [ ['Ok'] ],  # default has no callbacks and shows Ok button
               cancel: str = None, # name of the button you want to designate as 'Cancel' (ends up being first)
               destructive: str = None, # name of the button you want to designate as destructive (ends up being red)
               style: int = UIAlertControllerStyleAlert, #or: UIAlertControllerStyleActionSheet
               completion: Callable[[],None] = None, # optional completion function that gets called when alert is presented
               animated: bool = True, # whether or not to animate the alert
               localRunLoop: bool = False, # whether or not to create a local event loop and block until dialog finishes.. useful for full stop error messages and/or password dialogs
               uiTextFieldHandlers : list = None, # if you want to create custom UITextFields in this alert, and the alert'ss type is UIAlertControllerStyleAlert, pass a list of fully annotated callbacks taking an objc_id as arg and returning None, one for each desired text fields you want to create
               ipadAnchor : object = None # A CGRect -- use this on ipad to specify an anchor if using UIAlertControllerStyleActionSheet
               ) -> ObjCInstance:
    if not NSThread.currentThread.isMainThread:
        raise Exception('utils.show_alert can only be called from the main thread!')
    alert = UIAlertController.alertControllerWithTitle_message_preferredStyle_(title, message, style)
    if uiTextFieldHandlers:
        if style != UIAlertControllerStyleAlert:
            raise ValueError('Cannot combine uiTextFieldHandlers with non-UIAlertControllerStyleAlert alerts!')
        for h in uiTextFieldHandlers:
            alert.addTextFieldWithConfigurationHandler_(Block(h)) # let's hope h is a callable of the right type with the right number of args else exception will be thrown here
    if type(actions) is dict:
        acts = []
        for k in actions.keys():
            if actions[k] is not None:
                acts.append([k,*actions[k]])
            else:
                acts.appens([k])
        actions = acts
    ct=0
    fun_args_dict = dict()
    got_callback = False
    for i,arr in enumerate(actions):
        has_callable = False
        fun_args = []
        if type(arr) is list or type(arr) is tuple:
            actTit = arr[0]
            fun_args = arr[1:]
            has_callable = True
        else:
            actTit = arr
        style = UIAlertActionStyleCancel if actTit == cancel else UIAlertActionStyleDefault
        style = UIAlertActionStyleDestructive if actTit == destructive else style
        def onAction(act_in : objc_id) -> None:
            act = ObjCInstance(act_in)
            fargs = fun_args_dict.get(act.ptr.value,[])
            nonlocal got_callback
            got_callback = True
            if len(fargs):
                #print("Calling action...")
                fargs[0](*fargs[1:])
        act = UIAlertAction.actionWithTitle_style_handler_(actTit,style,onAction)
        fun_args_dict[act.ptr.value] = fun_args
        alert.addAction_(act)
        ct+=1
    def onCompletion() -> None:
        #print("On completion called..")
        nonlocal got_callback
        if not actions: got_callback = True
        if completion is not None:
            #print("Calling completion callback..")
            completion()
    if is_ipad() and alert.preferredStyle == UIAlertControllerStyleActionSheet:
        popover = alert.popoverPresentationController()
        if isinstance(ipadAnchor, UIBarButtonItem):
            popover.barButtonItem = ipadAnchor
        else:
            popover.sourceView = vc.view
            if isinstance(ipadAnchor, CGRect):
                rect = ipadAnchor
            else:
                rect = vc.view.frame
                rect = CGRectMake(rect.size.width/2.0,rect.size.height/4.0,0.0,0.0)
            popover.sourceRect = rect
    vc.presentViewController_animated_completion_(alert,animated,onCompletion)
    if localRunLoop:
        while not got_callback:
            NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))
        return None
    return alert

# Useful for doing a "Please wait..." style screen that takes itself offscreen automatically after a delay
# (may end up using this for some info alerts.. not sure yet)
def show_timed_alert(vc : ObjCInstance, title : str, message : str,
                     timeout : float, style : int = UIAlertControllerStyleAlert, animated : bool = True) -> ObjCInstance:
    assert NSThread.currentThread.isMainThread
    alert = None
    def completionFunc() -> None:
        def dismisser() -> None:
            vc.dismissViewControllerAnimated_completion_(animated,None)
        call_later(timeout, dismisser)
    alert=show_alert(vc=vc, title=title, message=message, actions=[], style=style, completion=completionFunc)
    return alert

###################################################
### Calling callables later or from the main thread
###################################################
def do_in_main_thread(func : Callable, *args) -> Any:
    if NSThread.currentThread.isMainThread:
        return func(*args)
    else:
        def VoidFun() -> None:
            func(*args)
        HelpfulGlue.performBlockInMainThread_sync_(VoidFun, False)
    return None

def do_in_main_thread_sync(func : Callable, *args) -> Any:
    if NSThread.currentThread.isMainThread:
        return func(*args)
    else:
        def VoidFun() -> None:
            func(*args)
        HelpfulGlue.performBlockInMainThread_sync_(VoidFun, True)
    return None

def do_in_main_thread_async(func : Callable, *args) -> None:
    def VoidFun() -> None:
        func(*args)
    HelpfulGlue.performBlockInMainThread_sync_(VoidFun, False)        

def call_later(timeout : float, func : Callable, *args) -> ObjCInstance:
    timer = None
    if not NSThread.currentThread.isMainThread:
        # NB: From NSRunLoop docs -- messing with the run loop from another thread is bad bad bad since NSRunLoop is not thread safe
        # so we force this scheduling of the NSTiemr to happen on the main thread...
        NSLog("****** WARNING WARNING WARNING -- utils.call_later() called from outside the main thread! FIXME!!!! ******")
        def inMain() -> None:
            nonlocal timer
            timer = call_later(timeout, func, *args)
        HelpfulGlue.performBlockInMainThread_sync_(inMain, True)        
    else:
        def OnTimer(t_in : objc_id) -> None:
            t = ObjCInstance(t_in)
            func(*args)
            t.invalidate()
        timer = NSTimer.timerWithTimeInterval_repeats_block_(timeout, False, OnTimer)
        NSRunLoop.mainRunLoop().addTimer_forMode_(timer, NSDefaultRunLoopMode)
    return timer

###
### Modal picker stuff
###
pickerCallables = dict()
class UTILSModalPickerHelper(UIViewController):
    
    items = objc_property()
    lastSelection = objc_property()
    needsDismiss = objc_property()
 
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self,'init'))
        self.items = None
        self.lastSelection = 0
        self.needsDismiss = False
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.finished()
        self.view = None
        self.needsDismiss = None
#        print("UTILSModalPickerHelper dealloc")
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def numberOfComponentsInPickerView_(self, p : ObjCInstance) -> int:
        return 1
    @objc_method
    def  pickerView_numberOfRowsInComponent_(self, p : ObjCInstance, component : int) -> int:
        assert component == 0
        return len(self.items)    
    @objc_method
    def pickerView_didSelectRow_inComponent_(self, p : ObjCInstance, row : int, component : int) -> None:
        assert component == 0 and row < len(self.items)
        self.lastSelection = row
                
    @objc_method
    def  pickerView_titleForRow_forComponent_(self, p : ObjCInstance, row : int, component : int) -> ObjCInstance:
        assert component == 0 and row < len(self.items)
        return ns_from_py(self.items[row])
    
    @objc_method
    def onOk_(self, but : ObjCInstance) -> None:
#        print ("Ok pushed")
        global pickerCallables
        cb = pickerCallables.get(self.ptr.value, None) 
        if cb is not None:
            sig = signature(cb)
            params = sig.parameters
            if len(params) > 0:
                cb(int(self.lastSelection))
            else:
                cb()
        self.finished()
        self.autorelease()
         
    @objc_method
    def onCancel_(self, but : ObjCInstance) -> None:
#        print ("Cancel pushed")        
        self.finished()
        self.autorelease()

    @objc_method
    def finished(self) -> None:
        global pickerCallables
        pickerCallables.pop(self.ptr.value, None)  
        if self.viewIfLoaded is not None and self.needsDismiss:
            self.dismissViewControllerAnimated_completion_(True, None)
        self.items = None
        self.lastSelection = None
        self.needsDismiss = False
        
###################################################
### Modal picker
###################################################
def present_modal_picker(parentVC : ObjCInstance,
                         items : list,
                         selectedIndex : int = 0,
                         okCallback : Callable[[int],None] = None,
                         okButtonTitle : str = "OK",
                         cancelButtonTitle : str = "Cancel") -> ObjCInstance:
    global pickerCallables
    assert parentVC is not None and items is not None and len(items)
    helper = UTILSModalPickerHelper.new()
    objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ModalPickerView",helper,None)
    if objs is None or not len(objs):
        raise Exception("Could not load ModalPickerView nib!")
    mpv = objs[0]
    p = mpv.viewWithTag_(200)
    okBut = mpv.viewWithTag_(1)
    okLbl = mpv.viewWithTag_(11)
    cancelBut = mpv.viewWithTag_(2)
    cancelLbl = mpv.viewWithTag_(22)
    assert p and okBut and cancelBut
    if okButtonTitle is not None and okLbl is not None: okLbl.text = okButtonTitle
    if cancelButtonTitle is not None and cancelLbl is not None: cancelLbl.text = cancelButtonTitle
    helper.view = mpv
    helper.items = items
    okBut.addTarget_action_forControlEvents_(helper, SEL(b'onOk:'), UIControlEventPrimaryActionTriggered)
    cancelBut.addTarget_action_forControlEvents_(helper, SEL(b'onCancel:'), UIControlEventPrimaryActionTriggered)
    p.delegate = helper
    p.dataSource = helper
    if okCallback is not None: pickerCallables[helper.ptr.value] = okCallback
    if selectedIndex > 0 and selectedIndex < len(items):
        p.selectRow_inComponent_animated_(selectedIndex, 0, False)
        helper.lastSelection = selectedIndex
    helper.modalPresentationStyle = UIModalPresentationOverCurrentContext
    helper.disablesAutomaticKeyboardDismissal = False
    parentVC.presentViewController_animated_completion_(helper, True, None)
    helper.needsDismiss = True
    return helper

###################################################
### Banner (status bar) notifications
###################################################
def show_notification(message : str,
                      duration : float = 2.0, # the duration is in seconds
                      color : tuple = None, # color needs to have r,g,b,a components -- length 4!
                      style : int = CWNotificationStyleStatusBarNotification,
                      animationStyle : int = CWNotificationAnimationStyleTop,
                      animationType : int = CWNotificationAnimationTypeReplace,
                      onTapCallback : Callable[[],None] = None, # the function to call if user taps notification -- should return None and take no args
                      multiline : bool = False) -> None:
    cw_notif = CWStatusBarNotification.new().autorelease()
    
    def onTap() -> None:
        #print("onTap")
        if onTapCallback is not None: onTapCallback()
        if not cw_notif.notificationIsDismissing:
            cw_notif.dismissNotification()
        
    if color is None or len(color) != 4 or [c for c in color if type(c) not in [float,int] ]:
        color = (0.0, 122.0/255.0, 1.0, 1.0)
      
    # set default blue color (since iOS 7.1, default window tintColor is black)
    cw_notif.notificationLabelBackgroundColor = UIColor.colorWithRed_green_blue_alpha_(*color)
    cw_notif.notificationStyle = style
    cw_notif.notificationAnimationInStyle = animationStyle
    cw_notif.notificationAnimationOutStyle = animationStyle
    cw_notif.notificationAnimationType = animationType
    cw_notif.multiline = multiline
    message = str(message)
    duration = float(duration)
    cw_notif.notificationTappedBlock = onTap
    cw_notif.displayNotificationWithMessage_forDuration_(message, duration)
 
 #######################################################
 ### NSLog emulation -- python wrapper for NSLog
 #######################################################

def NSLog(fmt : str, *args) -> int:
    args = list(args)
    if isinstance(fmt, ObjCInstance):
        fmt = str(py_from_ns(fmt))
    fmt = fmt.replace("%@","%s")
    for i,a in enumerate(args):
        if isinstance(a, ObjCInstance):
            try:
                args[i] = str(a.description)
            except Exception as e0:
                #print("Exception on description call: %s"%str(e0))
                try:
                    args[i] = str(py_from_ns(a))
                except Exception as e:
                    print("Cannot convert NSLog argument %d to str: %s"%(i+1,str(e)))
                    args[i] = "<Unknown>"
    try:
        formatted = ns_from_py("{}".format(fmt%tuple(args)))
        # NB: we had problems with ctypes and variadic functions due to ARM64 ABI weirdness. So we do this.
        HelpfulGlue.NSLogString_(formatted)
    except Exception as e:
        print("<NSLog Emul Exception> : %s"%(str(e)))
        formatted = "[NSLog Unavailable] {}".format(fmt%tuple(args))
        print(formatted)

####################################################################
# NS Object Cache
#
# Store frequently used objc instances in a semi-intelligent, auto-
# retaining dictionary, complete with automatic low-memory-warning
# detection.
####################################################################
class NSObjCache:
    def __init__(self, maxSize : int = 4, name : str = "Unnamed"):
        self._cache = dict()
        maxSize = 4 if type(maxSize) not in [float, int] or maxSize < 1 else int(maxSize)
        self._max = maxSize
        self._name = name
        self._last = None
        def lowMemory(notificaton : ObjCInstance) -> None:
            # low memory warning -- loop through cache and release all cached images
            ct = 0
            for k in self._cache.keys():
                self._cache[k].release()
                ct += 1
            self._cache = dict()
            if ct: NSLog("Low Memory: Flushed %d objects from '%s' NSObjCache."%(ct,self._name))
     
        self._token = NSNotificationCenter.defaultCenter.addObserverForName_object_queue_usingBlock_(
            UIApplicationDidReceiveMemoryWarningNotification,
            UIApplication.sharedApplication,
            None,
            lowMemory
        ).retain()
    def __del__(self):
        while len(self): self.release1()
        if self._token is not None:
            NSNotificationCenter.defaultCenter.removeObserver_(self._token.autorelease())
            self._token = None
    def release1(self):
        keez = list(self._cache.keys())
        while len(keez): # this normally only iterates once
            k = keez[random.randrange(len(keez))]
            if len(keez) > 1 and k is not None and self._last is not None and k == self._last:
                # never expire the 'latest' item from the cache, unless the cache is of size 1
                continue
            self._cache.pop(k).release()
            if k == self._last: self._last = None
            break # end after 1 successful iteration
    def put(self, key, obj : ObjCInstance):
        if self._cache.get(key,None) is not None: return
        while len(self) >= self._max:
            self.release1()
            #print("NSObjCache %s expired an object from full cache"%(self._name))
        self._cache[key] = obj.retain()
        #print("Cache %s size now %d"%(self._name,len(self)))
    def get(self, key) -> ObjCInstance: # returns None on cache miss
        ret = self._cache.get(key, None)
        #if ret is not None: print("NSObjCache %s hit"%(self._name))
        #else: print("NSObjCache %s miss"%(self._name))
        self._last = key
        return ret
    def __len__(self):
        return len(self._cache)

#############################
# Shows a QRCode 
#############################
_qr_cache = NSObjCache(10,"QR UIImage Cache")
def present_qrcode_vc_for_data(vc : ObjCInstance, data : str, title : str = "QR Code") -> ObjCInstance:
    uiimage = get_qrcode_image_for_data(data)
    qvc = UIViewController.new().autorelease()
    qvc.title = title
    iv = UIImageView.alloc().initWithImage_(uiimage).autorelease()
    iv.autoresizeMask = UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight|UIViewAutoresizingFlexibleLeftMargin|UIViewAutoresizingFlexibleRightMargin|UIViewAutoresizingFlexibleTopMargin|UIViewAutoresizingFlexibleBottomMargin
    iv.contentMode = UIViewContentModeScaleAspectFit
    iv.opaque = True
    iv.backgroundColor = UIColor.whiteColor
    qvc.view = iv
    nav = UINavigationController.alloc().initWithRootViewController_(qvc).autorelease()
    vc.presentViewController_animated_completion_(nav,True,None)
    return qvc

def get_qrcode_image_for_data(data : str) -> ObjCInstance:
    global _qr_cache
    if not isinstance(data, (str, bytes)):
        raise TypeError('argument to get_qrcode_for_data should be of type str or bytes!')
    if type(data) is bytes: data = data.decode('utf-8')
    uiimage = _qr_cache.get(data)
    if uiimage is None:
        qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathFillImage)
        qr.add_data(data)
        img = qr.make_image()
        fname = ""
        tmp, fname = tempfile.mkstemp()
        img.save(fname)
        os.close(tmp)
        with open(fname, 'r') as tmp_file:
            contents = tmp_file.read()
        os.remove(fname)
        uiimage = UIImage.imageWithSVGString_targetSize_fillColor_cachedName_(
            contents,
            CGSizeMake(256,256),
            UIColor.blackColor,
            None
        )
        _qr_cache.put(data, uiimage)
    return uiimage

#########################################################################################
# Poor man's signal/slot support
#   For our limited ObjC objects which can't have Python attributes
#########################################################################################
_cb_map = dict()
def add_callback(obj : ObjCInstance, name : str, callback : Callable) -> None:
    global _cb_map
    if name is None: raise ValueError("add_callback: name parameter must be not None")
    if callable(callback):
        m = _cb_map.get(obj.ptr.value, dict())
        m[name] = callback
        _cb_map[obj.ptr.value] = m 
    else:
        remove_callback(obj, name)        

def remove_all_callbacks(obj : ObjCInstance) -> None:
    global _cb_map
    _cb_map.pop(obj.ptr.value, None)

def remove_callback(obj : ObjCInstance, name : str) -> None:
    global _cb_map
    if name is not None:
        m = _cb_map.get(obj.ptr.value, None)
        if m is None: return
        m.pop(name, None)
        if len(m) <= 0:
            _cb_map.pop(obj.ptr.value, None)
        else:
            _cb_map[obj.ptr.value] = m
    else:
        remove_all_callbacks(obj)

def get_callback(obj : ObjCInstance, name : str) -> Callable:
    global _cb_map
    def dummyCB(*args) -> None:
        pass
    if name is None: raise ValueError("get_callback: name parameter must be not None")
    return _cb_map.get(obj.ptr.value, dict()).get(name, dummyCB)

#########################################################
# TaskThread Stuff
#  -- execute a python task in a separate (Python) Thread
######################################################### 
class TaskThread:
    '''Thread that runs background tasks.  Callbacks are guaranteed
    to happen in the main thread.'''
    
    Task = namedtuple("Task", "task cb_success cb_done cb_error")

    def __init__(self, on_error=None):
        self.on_error = on_error
        self.tasks = queue.Queue()
        self.worker = threading.Thread(target=self.run, name="TaskThread worker", daemon=True)
        self.start()
    
    def __del__(self):
        #NSLog("TaskThread __del__")
        if self.worker:
            if self.worker.is_alive():
                NSLog("TaskThread worker was running, force cancel...")
                self.stop()
                #self.wait()
            self.worker = None

    def start(self):
        if self.worker and not self.worker.is_alive():
            self.worker.start()
            return True
        elif not self.worker:
            raise ValueError("The Thread worker was None!")
        
    def add(self, task, on_success=None, on_done=None, on_error=None):
        on_error = on_error or self.on_error
        self.tasks.put(TaskThread.Task(task, on_success, on_done, on_error))

    def run(self):
        while True:
            task = self.tasks.get()
            if not task:
                break
            try:
                result = task.task()
                do_in_main_thread(self.on_done, result, task.cb_done, task.cb_success)
            except:
                do_in_main_thread(self.on_done, sys.exc_info(), task.cb_done, task.cb_error)
        NSLog("Exiting TaskThread worker thread...")
                
    def on_done(self, result, cb_done, cb):
        # This runs in the main thread.
        if cb_done:
            cb_done()
        if cb:
            cb(result)

    def stop(self):
        if self.worker and self.worker.is_alive():
            self.tasks.put(None)
        
    def wait(self):
        if self.worker and self.worker.is_alive():
            self.worker.join()
            self.worker = None

    @staticmethod
    def test():
        def onError(result):
            NSLog("onError called, result=%s",str(result))
        tt = TaskThread(onError)
        def onDone():
            nonlocal tt
            NSLog("onDone called")
            tt.stop()
            tt.wait()
            NSLog("test TaskThread joined ... returning.. hopefully cleanup will happen")
            tt = None # cleanup?
        def onSuccess(result):
            NSLog("onSuccess called, result=%s",str(result))
        def task():
            NSLog("In task thread.. sleeping once every second for 10 seconds")
            for i in range(0,10):
                NSLog("Iter: %d",i)
                time.sleep(0.2)
            return "Yay!"
        tt.add(task, onSuccess, onDone, onError)

class WaitingDialog:
    '''Shows a please wait dialog whilst runnning a task.  It is not
    necessary to maintain a reference to this dialog.'''
    def __init__(self, vc, message, task, on_success=None, on_error=None):
        assert vc
        title = _("Please wait")
        self.vc = vc
        self.thread = TaskThread()
        def onPresented() -> None:
            self.thread.add(task, on_success, self.dismisser, on_error)
        self.alert=show_alert(vc = self.vc, title = title, message = message, actions=[], completion=onPresented)

    def __del__(self):
        #print("WaitingDialog __del__")
        pass

    def wait(self):
        self.thread.wait()

    def on_finished(self) -> None:
        self.thread.stop()
        self.wait()
        self.alert = None
        self.thread = None

    def dismisser(self) -> None:
        def compl() -> None:
            self.on_finished()
        self.vc.dismissViewControllerAnimated_completion_(True, compl)
###
# NS -> py cache since our obj-c objects can't store python attributes :/
###
_nspy_dict = dict()
def nspy_get(ns : ObjCInstance) -> Any:
    global _nspy_dict
    return _nspy_dict.get(ns.ptr.value,None)
def nspy_put(ns : ObjCInstance, py : Any) -> None:
    global _nspy_dict
    _nspy_dict[ns.ptr.value] = py
def nspy_pop(ns : ObjCInstance) -> Any:
    global _nspy_dict
    return _nspy_dict.pop(ns.ptr.value,None)
def nspy_get_byname(ns : ObjCInstance, name : str) -> Any:
    m = nspy_get(ns)
    ret = None
    if isinstance(m, dict):
        ret = m.get(name,None)
    return ret
def nspy_put_byname(ns : ObjCInstance, py : Any, name : str) -> None:
    m = nspy_get(ns)
    needPutBack = False
    if m is None:
        m = dict()
        needPutBack = True
    if isinstance(m, dict):
        m[name] = py
    if needPutBack:  nspy_put(ns, m)
def nspy_pop_byname(ns : ObjCInstance, name : str) -> Any:
    m = nspy_get(ns)
    ret = None
    if m and isinstance(m, dict):
        ret = m.pop(name,None)
        if not m: nspy_pop(ns) # clean up when dict is empty
    return ret

####################################################################
# Another take on signals/slots -- Python-only signal/slot mechanism
####################################################################
class PySig:
    def __init__(self):
        self.clear()
    def clear(self) -> None:
        try:
            del self.slots
            del self.keys
        except AttributeError:
            pass
        self.slots = set()
        self.keys = dict()
    def connect(self, func : Callable, key : Any = None) -> None:
        ''' Note: the func arg, for now, needs to take explicit args and no *args, **kwags business as it's not yet supported.'''
        if not callable(func):
            raise ValueError("Passed-in arg to PySig connect is not a callable!")
        if key is not None:
            try:
                self.slots.remove(self.keys[key])
            except:
                pass
            self.keys[key] = func
        self.slots.add(func)
    def disconnect(self, func_or_key : Any = None) -> None:
        if func_or_key is None:
            self.clear()
            return
        func = None
        if callable(func_or_key):
            func = func_or_key
        else:
            func = self.keys.pop(func_or_key, None)
        try:
            self.slots.remove(func)
        except KeyError:
            pass
    def emit_common(self, require_sync : bool, *args) -> None:
        # guard against slots requesting themselves to be removed while this loop is iterating
        slots = self.slots.copy() #if require_sync or NSThread.currentThread.isMainThread else self.slots
        for slot in slots:
            sig = signature(slot)
            #if len(sig.parameters) > len(args):
            #    raise ValueError('PySig: One of the slots requires more parameters than were passed-in to emit!')
            if require_sync:
                do_in_main_thread_sync(slot, *args[:len(sig.parameters)])
            else:
                do_in_main_thread(slot,*args[:len(sig.parameters)])
    def emit(self, *args) -> None:
        self.emit_common(False, *args)
    def emit_sync(self, *args) -> None:
        self.emit_common(True, *args)

class MyNSObs(NSObject):
    @objc_method
    def dealloc(self) -> None:
        #print("MyNSObs dealloc")
        sig = nspy_pop(self)
        if sig is not None:
            #print("MyNSObs -- sig was found...")
            sig.emit(sig.ptr)
            sig.observer = None
        else:
            print("MyNSObs -- sig was None!")
        send_super(__class__,self,'dealloc')

class NSDeallocObserver(PySig):
    ''' Provides the ability to observe the destruction of an objective-c object instance, and be notified of said
        object's destruction on the main thread via our Qt-like 'signal' mechanism. Note sure how useful this really is except
        for debugging purposes.
        Note that it is not necessary to keep a reference to this object around as it automatically gets associated with
        internal data structures and auto-removes itself once the signal is emitted. The signal itself has 1 param, the objc_id
        of the watched object. The watched object may or may not still be alive when the signal is emitted, however.'''
    def __init__(self, ns : ObjCInstance):
        if not isinstance(ns, (ObjCInstance, objc_id)):
            raise ValueError("Argument for NSDeallocObserver must be an ObjCInstance or objc_id")
        super().__init__()
        self.ptr = ns.ptr if isinstance(ns, ObjCInstance) else ns
        import rubicon.objc.runtime as rt
        self.observer = MyNSObs.new().autorelease()
        rt.libobjc.objc_setAssociatedObject(self.ptr, self.observer.ptr, self.observer.ptr, 0x301)
        nspy_put(self.observer, self) # our NSObject keeps a strong reference to us

    '''
    # This is here for debugging purposes.. Commented out as __del__ is dangerous if it has external dependencies
    def __del__(self):
        #print ("NSDeallocObserver __del__")
        if self.observer:
            print("NSDeallocObserver __del__: self.observer was not nil!")
            nspy_pop(self.observer)
        #super().__del__()
    '''
    
def set_namedtuple_field(nt : object, fieldname : str, newval : Any) -> object:
    try:
        d = nt._asdict()
    except:
        raise ValueError('set_namedtuple_field, first argument does not appear to be a valid namedtuple!')
    if not isinstance(fieldname, str):
         raise ValueError('set_namedtuple_field, fieldname (second arg) must be a string!')
    if fieldname not in d:
        raise ValueError('%s is not a field in namedtuple %s'%(str(fieldname),type(nt).__qualname__))
    else:
        d[fieldname] = newval
        return type(nt)(**d)
