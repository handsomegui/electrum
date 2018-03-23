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
from .uikit_bindings import *
from . import utils
from . import gui
from .custom_objc import *

from electroncash.i18n import _

import socket

from electroncash.networks import NetworkConstants
from electroncash.network import serialize_server, deserialize_server

TAG_HELP_STATUS = 112
TAG_HELP_SERVER = 122
TAG_HELP_BLOCKCHAIN = 132
TAG_HELP_AUTOSERVER = 212
TAG_HOST_TF = 221
TAG_PORT_TF = 222

BUTTON_TAGS = (TAG_HELP_STATUS, TAG_HELP_SERVER, TAG_HELP_BLOCKCHAIN, TAG_HELP_AUTOSERVER)

def parent() -> object:
    return gui.ElectrumGui.gui

class NetworkDialogVC(UIViewController):
    
    connectedTV = objc_property()
    untranslatedMap = objc_property()
    peersTV = objc_property()
    hostTF = objc_property()
    portTF = objc_property()

    @objc_method
    def dealloc(self) -> None:
        self.connectedTV = None
        self.untranslatedMap = None
        self.peersTV = None
        self.hostTF = None
        self.portTF = None
        utils.nspy_pop(self)
        send_super(__class__, self, 'dealloc')
   
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("NetworkDialog",None,None)
        v = objs[0]
        sv = UIScrollView.alloc().initWithFrame_(CGRectMake(0,0,320,580)).autorelease()
        sv.contentSize = CGSizeMake(320,700)
        sv.addSubview_(v)
        
        self.connectedTV = v.viewWithTag_(140)
        self.connectedTV.dataSource = self
        self.connectedTV.delegate = self
        self.peersTV = v.viewWithTag_(240)
        self.peersTV.dataSource = self
        self.peersTV.delegate = self
        
        self.view = sv

        # connect buttons to functions
        views = self.view.allSubviewsRecursively()
        showHelpBlock = Block(showHelpForButton)
        def onAutoServerSW(oid : objc_id) -> None:
            tags = (220, 221, 222, 230, 240)
            sw = ObjCInstance(oid)
            for t in tags:
                v = self.view.viewWithTag_(t)
                if v is None: continue
                utils.uiview_set_enabled(v, not sw.isOn())
        def onTfChg(oid : objc_id) -> None:
            tf = ObjCInstance(oid)
            print("tf %d changed txt = %s"%(int(tf.tag),str(tf.text)))
        onTfChgBlock = Block(onTfChg)
        for v in views:
            if isinstance(v, UIButton) and v.tag in BUTTON_TAGS:
                v.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, showHelpBlock)
            elif isinstance(v, UISwitch) and v.tag is 210:
                v.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onAutoServerSW)
            elif isinstance(v, UITextField) and v.tag in (TAG_HOST_TF, TAG_PORT_TF):
                v.delegate = self
                if v.tag is TAG_HOST_TF: self.hostTF = v
                elif v.tag is TAG_PORT_TF: self.portTF = v
                v.handleControlEvent_withBlock_(UIControlEventEditingChanged,onTfChgBlock)

        self.translateUI()

    @objc_method
    def translateUI(self) -> None:
        view = self.viewIfLoaded
        if view is None: return
        utmap = self.untranslatedMap
        if utmap is None: utmap = dict()
        def doTranslate(ns : ObjCInstance, txt_in : str) -> str:
            txt = utmap.get(ns.ptr.value, None)
            if txt is None:
                txt = txt_in
                utmap[ns.ptr.value] = txt
            txt = txt.strip()
            if not txt: return None
            hadColon = False
            if txt[-1] == ':':
                hadColon = True
                txt = txt[:len(txt)-1]
            return  _(txt) + (':' if hadColon else '')     
        views = view.allSubviewsRecursively()
        for v in views:
            if isinstance(v, UILabel):
                txt = doTranslate(v, v.text)
                if txt: v.text = txt
            if isinstance(v, UITextField):
                txt = doTranslate(v, v.placeholder)
                if txt: v.placeholder = txt
        self.untranslatedMap = utmap
    
    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        self.view.flashScrollIndicators()
        self.connectedTV.flashScrollIndicators()
        self.peersTV.flashScrollIndicators()
    
    @objc_method
    def numberOfSectionsInTableView_(self, tv) -> int:
        return 1
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance,section : int) -> ObjCInstance:
        if tv.ptr == self.connectedTV.ptr:
            return _("Connected node") + ", " + _("Height")
        elif tv.ptr == self.peersTV.ptr:
            return _("Host") + ", " + _("Port")
        print("*** WARNING *** tableView is unknown in tableView_titleForHeaderInSection_!!")
        return _("Unknown")
        
    @objc_method
    def tableView_numberOfRowsInSection_(self, tv : ObjCInstance, section : int) -> int:
        return 10 if tv.ptr == self.connectedTV.ptr else 100
    
    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tv, indexPath) -> ObjCInstance:
        cell = None
        if tv.ptr == self.connectedTV.ptr:
            identifier = str(__class__) + "ConnectedNode_Height"
            cell = tv.dequeueReusableCellWithIdentifier_(identifier)
            if cell is None:
                objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ServerPortCell22px",None,None)
                cell = objs[0]
            l1 = cell.viewWithTag_(150)
            l2 = cell.viewWithTag_(160)
            l2.text = str(3233355+indexPath.row)
            
            dummies = utils.nspy_get_byname(self, 'servers')
            if not dummies:
                dummies = [
                        "foo.bar.nz",
                        "someserver.somwehre.com",
                        "112.123.145.16",
                        "cgpgray.is.talking.co.uk",
                        "electrumx.cash.com",
                        "this.is.a.test"
                ]
                utils.nspy_put_byname(self, dummies, 'servers')
            l1.text = dummies[indexPath.row%len(dummies)]
            cell.contentView.backgroundColor = UIColor.clearColor if not indexPath.row % 2 else UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.0,0.03)
        elif tv.ptr == self.peersTV.ptr:
            identifier = str(__class__) + "PeerHost_Port"
            cell = tv.dequeueReusableCellWithIdentifier_(identifier)
            if cell is None:
                objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ServerPortCell22px",None,None)
                cell = objs[0]
            l1 = cell.viewWithTag_(150)
            l2 = cell.viewWithTag_(160)
            ports=(50002,51002,60002)
            l2.text = str(ports[indexPath.row%len(ports)])
            
            dummies = utils.nspy_get_byname(self, 'servers')
            if not dummies:
                dummies = [
                        "foo.bar.nz",
                        "someserver.somwehre.com",
                        "112.123.145.16",
                        "cgpgray.is.talking.co.uk",
                        "electrumx.cash.com",
                        "this.is.a.test"
                ]
                utils.nspy_put_byname(self, dummies, 'servers')
            l1.text = dummies[indexPath.row%len(dummies)]
            cell.contentView.backgroundColor = UIColor.clearColor if not indexPath.row % 2 else UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.0,0.03)            
        return cell

    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath) -> None:
        print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath) -> None:
        print("DID SELECT ROW CALLED FOR SECTION %s, ROW %s"%(str(indexPath.section),str(indexPath.row)))
        if tv.ptr == self.connectedTV.ptr:
            dummies = utils.nspy_get_byname(self, 'servers')
            server = dummies[indexPath.row%len(dummies)]
            def wantsToChangeServer() -> None:
                print("Server change for %s selected -- TOOD: IMPLEMENT ME!!"%(server))
            parent().question(message = _("Do you wish to use\n%s\nas the wallet server?")%(str(server)),
                              title = str(_("Use as server") + '?'),
                              yesno = True,
                              onOk = wantsToChangeServer)
            tv.deselectRowAtIndexPath_animated_(indexPath, True)
            
    @objc_method
    def textFieldDidBeginEditing_(self, tf : ObjCInstance) -> None:
        if UI_USER_INTERFACE_IDIOM() != UIUserInterfaceIdiomPhone:  return
        # try and center the text fields on the screen.. this is an ugly HACK.
        # todo: fixme!
        sv = self.viewIfLoaded 
        if sv and isinstance(sv, UIScrollView):
            sb = UIScreen.mainScreen.bounds
            v = sv.subviews()[0]
            frame = v.frame
            frame.origin.y = 700 - frame.size.height
            o = UIApplication.sharedApplication.statusBarOrientation
            if o in [UIInterfaceOrientationLandscapeLeft,UIInterfaceOrientationLandscapeRight]:
                frame.origin.y -= 100
                #print("WAS LANDSCAPE")
            #print("frame=%f,%f,%f,%f"%(frame.origin.x,frame.origin.y,frame.size.width,frame.size.height))
            sv.scrollRectToVisible_animated_(frame, True)
        
    @objc_method
    def textFieldDidEndEditing_(self, tf : ObjCInstance) -> None:
        print("textFieldDidEndEditing", tf.tag, tf.text)
        return True
    
    @objc_method
    def textFieldShouldReturn_(self, tf: ObjCInstance) -> bool:
        print("textFieldShouldReturn", tf.tag)
        tf.resignFirstResponder()
        return True
            
def showHelpForButton(oid : objc_id) -> None:
    tag = int(ObjCInstance(oid).tag)
    msg = _("Unknown")
    if tag is TAG_HELP_STATUS:
        msg = ' '.join([
            _("Electrum connects to several nodes in order to download block headers and find out the longest blockchain."),
            _("This blockchain is used to verify the transactions sent by your transaction server.")
        ])
    elif tag is TAG_HELP_SERVER:
        msg = _("Electrum sends your wallet addresses to a single server, in order to receive your transaction history.")
    elif tag is TAG_HELP_BLOCKCHAIN:
        msg = _('This is the height of your local copy of the blockchain.')
    elif tag is TAG_HELP_AUTOSERVER:
        msg = ' '.join([
            _("If auto-connect is enabled, Electrum will always use a server that is on the longest blockchain."),
            _("If it is disabled, you have to choose a server you want to use. Electrum will warn you if your server is lagging.")
        ])
    msg = msg.replace("Electrum","Electron Cash")
    parent().show_message(msg)