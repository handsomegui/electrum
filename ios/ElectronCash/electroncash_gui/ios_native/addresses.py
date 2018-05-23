from . import utils
from . import gui
from . import private_key_dialog
from . import sign_decrypt_dialog
from . import history
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
import electroncash.exchange_rate
from electroncash.i18n import _, language
from electroncash.address import Address

import time
import html
import sys
import enum
from collections import namedtuple

from .uikit_bindings import *
from .custom_objc import *

_TYPES = ("Any","Receiving","Change")
_STATUSES = ("All", "Funded", "Unused", "Used")
_TYPES_BY_NAME = dict()
_STATUSES_BY_NAME = dict()

for i,k in enumerate(_TYPES):
    _TYPES_BY_NAME[k] = i
for i,k in enumerate(_STATUSES):
    _STATUSES_BY_NAME[k] = i

class AddressDetail(UIViewController):
    
    defaultBG = objc_property()
    blockRefresh = objc_property()
    needsRefresh = objc_property()
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.title = "Address Details"
        gui.ElectrumGui.gui.sigAddresses.connect(lambda:self.refresh(), self)
        gui.ElectrumGui.gui.sigHistory.connect(lambda:self.refresh(), self)

        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("AddressDetail dealloc")
        gui.ElectrumGui.gui.sigAddresses.disconnect(self)
        gui.ElectrumGui.gui.sigHistory.disconnect(self)
        utils.nspy_pop(self)
        self.title = None
        self.view = None
        self.defaultBG = None
        self.blockRefresh = None
        self.needsRefresh = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("AddressDetail",None,None)
        v = None
        gr = None
        
        for o in objs:
            if isinstance(o, UIView):
                v = o
            elif isinstance(o, UIGestureRecognizer):
                gr = o
        if v is None or gr is None:
            raise ValueError('AddressDetail XIB is missing either the primary view or the expected gesture recognizer!')
        
        gr.addTarget_action_(self, SEL(b'onTapAddress'))

        parent = gui.ElectrumGui.gui
   
        entry = utils.nspy_get_byname(self, 'entry')        

        tf = v.viewWithTag_(210)
        tf.delegate = self

        but = v.viewWithTag_(520)
        def toggleFreeze(oid : objc_id) -> None:
            _ToggleFreeze(entry)
            self.onToggleFreeze()
        but.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, toggleFreeze)
        
        butMore = v.viewWithTag_(150)
        def onButMore(oid : objc_id) -> None:
            self.onTapAddress()
        butMore.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onButMore)

        butCpy = v.viewWithTag_(120)
        butQR = v.viewWithTag_(130)
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, None)  # clear existing action
        def onCpy(oid : objc_id) -> None:
            self.onCpyBut()
        def onQR(oid : objc_id) -> None:
            self.onQRBut()
        butCpy.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onCpy) # bind actin to closure 
        butQR.handleControlEvent_withBlock_(UIControlEventPrimaryActionTriggered, onQR)  # bind action to closure
        
        tv = v.viewWithTag_(1000)
        
        # Re-use of TxHistoryHelper below...
        helper = history.NewTxHistoryHelper(tv = tv, vc = self, noRefreshControl = True, domain = [entry.address], cls=history.TxHistoryHelperWithHeader)

        self.view = v
                
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        self.refresh()
        
    @objc_method
    def refresh(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        if self.blockRefresh:
            self.needsRefresh = True
            return
        entry = utils.nspy_get_byname(self, 'entry')
 
        lbl = v.viewWithTag_(100)
        lbl.text = _("Address") + ":"        
        lbl = v.viewWithTag_(110)
        lbl.text = entry.addr_str
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
        lbl.text = _("Description") + ":"
        tf = v.viewWithTag_(210)
        tf.placeholder = _("Tap to add a description")
        tf.text = entry.label

        lbl = v.viewWithTag_(300)
        lbl.text = _("NumTx") + ":"
        lbl = v.viewWithTag_(310)
        lbl.text = str(entry.num_tx)
        
        lbl = v.viewWithTag_(400)
        lbl.text = _("Balance") + ":"
        lbl = v.viewWithTag_(410)
        lbl.text = entry.balance_str + ((' (' + entry.fiat_balance_str + ')') if entry.fiat_balance_str else '')
        
        lbl = v.viewWithTag_(500)
        lbl.text = _("Flags") + ":"
        lbl = v.viewWithTag_(510)
        flags = []
        if entry.is_change: flags.append(_("Change"))
        if entry.is_frozen: flags.append(_("Frozen"))
        lbl.text = ', '.join(flags)
        
        tv = v.viewWithTag_(1000)
        # This was here for old UI style.. removed for now as we transition to new
        #tv.backgroundColor = bgColor
        
        self.refreshButs()
        tv.reloadData() # might be a sometimes-redundant call since WalletsTxHelper also calls reload data..
        
        self.needsRefresh = False
        
    @objc_method
    def onTapAddress(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        _ShowAddressContextMenu(entry, self, ipadAnchor = self.view.viewWithTag_(150).frame, toggleFreezeCallback = lambda:self.onToggleFreeze())
        
    @objc_method
    def onCpyBut(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        UIPasteboard.generalPasteboard.string = entry.addr_str
        utils.show_notification(message=_("Text copied to clipboard"))
    @objc_method
    def onQRBut(self) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        qrvc = utils.present_qrcode_vc_for_data(vc=self,
                                                data=entry.addr_str,
                                                title = _('QR code'))
        gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)

    @objc_method
    def onToggleFreeze(self) -> None:
        parent = gui.ElectrumGui.gui
        if parent.wallet:
            entry = utils.nspy_get_byname(self, 'entry')
            entry = utils.set_namedtuple_field(entry, 'is_frozen', not entry.is_frozen)
            utils.nspy_put_byname(self, entry, 'entry')
            self.refresh()
        
    @objc_method
    def refreshButs(self) -> None:
        v = self.viewIfLoaded
        if v is None: return
        parent = gui.ElectrumGui.gui
        watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True
        but = v.viewWithTag_(520)
        entry = utils.nspy_get_byname(self, 'entry')
        but.setTitle_forState_(_("Freeze") if not entry.is_frozen else _("Unfreeze"), UIControlStateNormal)
        but.setHidden_(watch_only)

        but = v.viewWithTag_(150)
        but.setTitle_forState_(_("Options") + "...", UIControlStateNormal)
        
    @objc_method
    def doRefreshIfNeeded(self) -> None:
        if self.needsRefresh: self.refresh()
        

    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        #print("hit return, value is {}".format(tf.text))
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidBeginEditing_(self, tf) -> None:
        self.blockRefresh = True # temporarily block refreshing since that kills our keyboard/textfield


    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        entry = utils.nspy_get_byname(self, 'entry')
        
        tf.text = tf.text.strip()
        new_label = tf.text
        entry = utils.set_namedtuple_field(entry, 'label', new_label)
        utils.nspy_put_byname(self, entry, 'entry')
        print ("new label for address %s = %s"%(entry.address.to_storage_string(), new_label))
        gui.ElectrumGui.gui.on_label_edited(entry.address, new_label)
        self.blockRefresh = False # unblock block refreshing
        self.refresh()
        
ModeNormal = 0
ModePicker = 1

# Addresses Tab -- shows addresses, etc
class AddressesVC(AddressesVCBase):
    needsRefresh = objc_property()
    blockRefresh = objc_property()
    mode = objc_property()
    refreshControl = objc_property()
    comboL = objc_property()
    comboR = objc_property()

    @objc_method
    def initWithMode_(self, mode : int):
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self:
            self.comboL = None
            self.comboR = None
            self.needsRefresh = False
            self.blockRefresh = False
            self.mode = int(mode)
            self.title = _("&Addresses").split('&')[1] if self.mode == ModeNormal else _("Choose Address")
            if self.mode == ModeNormal:
                self.tabBarItem.image = UIImage.imageNamed_("tab_addresses_new")
                bb = UIBarButtonItem.alloc().initWithTitle_style_target_action_(_GetBBTitle(), UIBarButtonItemStylePlain, self, SEL(b'toggleCashAddr')).autorelease()
                bb.possibleTitles = NSSet.setWithArray_(_GetBBTitle('*'))
                d = { NSFontAttributeName : UIFont.systemFontOfSize_(14.0) }
                bb.setTitleTextAttributes_forState_(d, UIControlStateNormal)
                d[NSFontAttributeName] = UIFont.systemFontOfSize_weight_(14.0, UIFontWeightRegular)
                bb.setTitleTextAttributes_forState_(d, UIControlStateHighlighted)
                self.navigationItem.rightBarButtonItem = bb

            self.refreshControl = UIRefreshControl.alloc().init().autorelease() 
            
            if self.mode == ModePicker:
                def onRefreshCtl() -> None:
                    self.refresh()
                self.refreshControl.handleControlEvent_withBlock_(UIControlEventValueChanged, onRefreshCtl)
     
            gui.ElectrumGui.gui.sigAddresses.connect(lambda:self.refresh(), self)
       
        return self

    @objc_method
    def dealloc(self) -> None:
        gui.ElectrumGui.gui.sigAddresses.disconnect(self)
        self.needsRefresh = None
        self.mode = None
        self.blockRefresh = None
        self.refreshControl = None
        self.comboL = None
        self.comboR = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def loadView(self) -> None:
        NSBundle.mainBundle.loadNibNamed_owner_options_("Addresses", self, None) # auto-attaches view
        self.tableView.refreshControl = self.refreshControl

        if self.mode == ModeNormal:
            uinib = UINib.nibWithNibName_bundle_("AddressesCell", None)
            self.tableView.registerNib_forCellReuseIdentifier_(uinib, "AddressesCell")
            
        # set up the combodrawer "child" vc's (they aren't really children in the iOS sense since I hate the way iOS treats embedded VCs)
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ComboDrawerPicker", None, None)
        for o in objs:
            if isinstance(o, ComboDrawerPicker):
                self.comboL = o
                break
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ComboDrawerPicker", None, None)
        for o in objs:
            if isinstance(o, ComboDrawerPicker):
                self.comboR = o
                break
            
        self.comboL.flushLeft = True
        
    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        self.setupComboCallbacks()
        self.setupComboItems()   
        
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtype=[c_bool])
        
        # hacky pulling in of attributed text string form the 'child' vc into our proxy stub
        self.topLblL.attributedText = self.comboL.attributedStringForTopTitle
        self.topLblR.attributedText = self.comboR.attributedStringForTopTitle
        
   

    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        try:
            addrData = _Get()
            return 1 if addrData.master[self.comboL.selection][self.comboR.selection] is not None else 0
        except:
            print("Error in addresses 1:",str(sys.exc_info()[1]))
        return 0
    
    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView : ObjCInstance, section : int) -> int:
        try:
            addrData = _Get()
            return max(1,len(addrData.master[self.comboL.selection][self.comboR.selection])) if addrData is not None else 0
        except:
            print("Error in addresses 2:",str(sys.exc_info()[1]))
        return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        #todo: - allow for label editing (popup menu?)
        identifier = "AddressesCell" if self.mode == ModeNormal else "Cell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        newCell = False
        if self.mode == ModePicker and cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle,identifier).autorelease()
            newCell = True

        try:
            addrData = _Get()
            entries = addrData.master[self.comboL.selection][self.comboR.selection]
        except:
            print("Error in addresses 3:",str(sys.exc_info()[1]))
            entries = list()
        
        if indexPath.row >= len(entries) or cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle,"NoMatchCell").autorelease()
            cell.textLabel.text = _("No Match")
            cell.textLabel.textColor = utils.uicolor_custom('dark')
            cell.detailTextLabel.text = _("No addresses match the specified criteria")
            cell.detailTextLabel.textColor = utils.uicolor_custom('light')
            return cell
                
        entry = entries[indexPath.row]
        if self.mode == ModeNormal:
            cell.address.attributedText = NSAttributedString.alloc().initWithString_attributes_(entry.addr_str, {
                NSFontAttributeName : UIFont.systemFontOfSize_(16.0),
                NSUnderlineStyleAttributeName : NSUnderlineStyleSingle,
                NSForegroundColorAttributeName : utils.uicolor_custom('nav')
            }).autorelease()
            if entry.label:
                cell.desc.setText_withKerning_(entry.label, utils._kern)
                cell.topCS.constant = 7
                cell.midCS.constant = 6
            else:
                cell.desc.text = ""
                cell.topCS.constant = 15
                cell.midCS.constant = 10
            cell.balanceTit.setText_withKerning_(_('Balance'), utils._kern)
            baltxt = entry.balance_str.strip() + " " + entry.base_unit
            cell.balance.attributedText = utils.hackyFiatAmtAttrStr(baltxt, entry.fiat_balance_str, '', 0.0, utils.uicolor_custom('light'), None, -0.5)
            xtra = []
            if entry.is_frozen:
                if entry.is_change:
                    xtra += [_('Change')]
                xtra += [_('Frozen')]
                cell.flags.textColor = utils.uicolor_custom('frozentext')
            else:
                cell.flags.textColor = utils.uicolor_custom('dark')
                if entry.is_change:
                    xtra += [_('Change')]
                if not entry.is_used:
                    xtra += [_('Unused')]
                xtra += [ str(entry.num_tx) + ' Txs']
            cell.flags.setText_withKerning_(', '.join(xtra) if xtra else '', utils._kern)
            
            
            if not cell.address.gestureRecognizers:
                gr = UITapGestureRecognizer.alloc().initWithTarget_action_(self, SEL(b'onTapAddress:')).autorelease()
                cell.address.addGestureRecognizer_(gr)
            cell.address.tag = (self.comboL.selection << 24) | (self.comboR.selection << 16) | (indexPath.row & 0xffff) # useful for onTapAddress to figure out what tapped it
            
            return cell
            
            
        else: # picker mode
            if newCell: 
                cell.accessoryType = UITableViewCellAccessoryNone
                cell.textLabel.adjustsFontSizeToFitWidth = True
                cell.textLabel.minimumScaleFactor = 0.9
                font = cell.textLabel.font
                cell.textLabel.font = UIFont.boldSystemFontOfSize_(font.pointSize)
                cell.detailTextLabel.adjustsFontSizeToFitWidth = True
                cell.detailTextLabel.minimumScaleFactor = 0.85
            cell.textLabel.text = str(entry.address)
            cell.detailTextLabel.text = "bal: " + entry.balance_str + ( (' (' + entry.fiat_balance_str + ')') if addrData.show_fx else '') + " numtx: " + str(entry.num_tx) + ((" - " + entry.label) if entry.label else "")
            cell.detailTextLabel.textColor = utils.uicolor_custom('dark')
            cell.backgroundColor = tableView.backgroundColor
            cell.textLabel.textColor = utils.uicolor_custom('dark')
            if entry.is_frozen:
                cell.backgroundColor = utils.uicolor_custom('frozen address')
                cell.textLabel.textColor = utils.uicolor_custom('frozen address text')
            if entry.is_change:
                cell.backgroundColor = utils.uicolor_custom('change address')                

        return cell
    
    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        if self.mode == ModeNormal:
            return 91.0
        return 44.0
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR SECTION %s, ROW %s"%(str(indexPath.section),str(indexPath.row)))
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
        try:
            addrData = _Get()
            section = addrData.master[self.comboL.selection][self.comboR.selection]
            if indexPath.row >= len(section):
                print("User tapped invalid cell.  Possibly the 'No Results' cell.")
                return
            entry = section[indexPath.row]
            if self.mode == ModeNormal:
                PushDetail(entry, self.navigationController)
            else:
                cb = utils.get_callback(self, 'on_picked')
                if callable(cb): cb(entry)
        except:
            print ("Exception encountered:",str(sys.exc_info()[1]))
    

    @objc_method
    def refresh(self):
        self.needsRefresh = True # mark that a refresh was called in case refresh is blocked
        if self.blockRefresh:
            return
        if self.refreshControl: self.refreshControl.endRefreshing()
        if self.tableView: 
            self.tableView.reloadData()
        if self.mode == ModeNormal and self.navigationItem.rightBarButtonItem:
            self.navigationItem.rightBarButtonItem.title = _GetBBTitle()
        #print("did address refresh")
        self.needsRefresh = False # indicate refreshing done

    # This method runs in the main thread as it's enqueue using our hacky "Heartbeat" mechanism/workaround for iOS
    @objc_method
    def doRefreshIfNeeded(self) -> None:
        if self.needsRefresh:
            self.refresh()
            #print ("ADDRESSES REFRESHED")
 
    @objc_method
    def toggleCashAddr(self) -> None:
        gui.ElectrumGui.gui.toggle_cashaddr(not gui.ElectrumGui.gui.prefs_get_use_cashaddr())
        
    @objc_method
    def onTapAddress_(self, gr : ObjCInstance) -> None:
        tag = gr.view.tag
        typ = (tag >> 24)&0xff
        stat = (tag >> 16)&0xff
        row = tag & 0xffff
        try:
            entry = _Get().master[typ][stat][row]
        except:
            print("onTapAddress exception:",str(sys.exc_info()[1]))
            return
        _ShowAddressContextMenu(entry, self, ipadAnchor = gr.view.frame)
 
    # -----------------------------------
    # COMBO DRAWER RELATED STUFF BELOW...
    # -----------------------------------
    @objc_method
    def setupComboItems(self) -> None:
        self.comboL.topTitle = _("Type")
        self.comboL.items = [ _(x) for x in _TYPES ]
        self.comboR.topTitle = _("Status")
        self.comboR.items = [ _(x) for x in _STATUSES ]
        parent = gui.ElectrumGui.gui
        if parent.config:
            self.comboL.selection = parent.config.get("AddressTab_Type_Filter", 0)
            self.comboR.selection = parent.config.get("AddressTab_Status_Filter", 0)

        
    @objc_method
    def setupComboCallbacks(self) -> None:
        # TODO: set up comboL and comboR vc's, and other misc. setup
        def closeLAnim() -> None:
            self.doComboClose_(self.comboL)
        def closeRAnim() -> None:
            self.doComboClose_(self.comboR)
        def bgTapChk(p : CGPoint) -> None:
            this = self.presentedViewController
            if isinstance(this, ComboDrawerPicker):
                fwl = self.topComboProxyL.convertRect_toView_(self.topComboProxyL.bounds, self.view)
                fwr = self.topComboProxyR.convertRect_toView_(self.topComboProxyR.bounds, self.view)
                p = self.view.convertPoint_fromView_(p, self.presentedViewController.view)
                that = None
                if CGRectContainsPoint(fwl, p): that = self.comboL
                elif CGRectContainsPoint(fwr, p): that = self.comboR
                if that:
                    # this hack to prevent screen flicker due to delays in present and dismiss viewcontroller.. very hacky but works!!
                    window = gui.ElectrumGui.gui.window
                    hax = UIView.alloc().initWithFrame_(window.bounds).autorelease()
                    hax.backgroundColor = that.view.backgroundColor
                    hax.opaque = False
                    hax2 = UIView.alloc().initWithFrame_(this.bottomView.convertRect_toView_(this.bottomView.bounds,None)).autorelease()
                    hax2.backgroundColor = this.bottomView.backgroundColor
                    hax.addSubview_(hax2)
                    window.addSubview_(hax)
                    that.view.backgroundColor = UIColor.clearColor
                    this.view.backgroundColor = UIColor.clearColor
                    def showIt() -> None:
                        def killHax() -> None:
                            this.view.backgroundColor = hax.backgroundColor
                            that.view.backgroundColor = hax.backgroundColor
                            hax.removeFromSuperview()
                        that.openAnimated_(False)
                        self.presentViewController_animated_completion_(that, False, killHax)
                    self.dismissViewControllerAnimated_completion_(False, showIt)
                    this.closeAnimated_(False)
                else:
                    self.doComboClose_(this)
        def selectionChanged(sel : int) -> None:
            which = self.presentedViewController
            if isinstance(which, ComboDrawerPicker):
                parent = gui.ElectrumGui.gui
                if parent.config:
                    whichKey = "AddressTab_Status_Filter" if which == self.comboR else "AddressTab_Type_Filter"
                    parent.config.set_key(whichKey, sel, True)
                whichLbl = self.topLblL if which == self.comboL else self.topLblR
                whichLbl.attributedText = which.attributedStringForTopTitle
                self.doComboClose_(which)
                # TODO: make the selection change take effect in how the table is filtered below..
                self.tableView.reloadData()

        self.comboL.backgroundTappedBlock = bgTapChk
        self.comboL.controlTappedBlock = closeLAnim
        self.comboL.controlTappedBlock = closeLAnim
        self.comboL.selectedBlock = selectionChanged
        self.comboR.backgroundTappedBlock = bgTapChk
        self.comboR.controlTappedBlock = closeRAnim
        self.comboR.selectedBlock = selectionChanged
  
    @objc_method
    def doComboOpen_(self, vc) -> None:
        semiclear = vc.view.backgroundColor.copy()
        vc.view.backgroundColor = UIColor.clearColor
        def compl() -> None:
            vc.view.backgroundColorAnimationToColor_duration_reverses_completion_(semiclear.autorelease(), 0.2, False, None)
            vc.openAnimated_(True)
        self.presentViewController_animated_completion_(vc, False, compl)
        
    @objc_method
    def doComboClose_(self, vc) -> None:
        self.doComboClose_animated_(vc, True)

    @objc_method
    def doComboClose_animated_(self, vc, animated : bool) -> None:
        # NB: weak ref self.modalDrawerVC will be auto-cleared by obj-c runtime after it is dismissed
        if animated:
            utils.call_later(0.050, self.dismissViewControllerAnimated_completion_,True, None)
        else:
            self.dismissViewControllerAnimated_completion_(False, None)    
        vc.closeAnimated_(animated)
    
    @objc_method
    def onTapComboProxyL(self) -> None:
        self.doComboOpen_(self.comboL)

    @objc_method
    def onTapComboProxyR(self) -> None:
        self.doComboOpen_(self.comboR)

class AddressData:
    
    Entry = namedtuple("Entry", "address addr_str addr_idx label balance_str fiat_balance_str num_tx is_frozen balance is_change is_used base_unit")
    
    def __init__(self, gui_parent):
        self.parent = gui_parent
        self.clear()
        
    def clear(self):
        self.show_fx = False        
        self.master = [ [list() for s in range(0,len(_STATUSES))]  for t in range(0, len(_TYPES)) ]
        
    def refresh(self):
        t0 = time.time()

        self.clear()

        wallet = self.parent.wallet
        daemon = self.parent.daemon
        if wallet is None: return

        receiving_addresses = wallet.get_receiving_addresses()
        change_addresses = wallet.get_change_addresses()

        numAddresses = 0
        base_unit = self.parent.base_unit()

        if daemon and daemon.fx and daemon.fx.get_fiat_address_config():
            fx = daemon.fx
            self.show_fx = True
        else:
            self.show_fx = False
            fx = None
        sequences = [0,1] if change_addresses else [0]
        for is_change in sequences:
            addr_list = change_addresses if is_change else receiving_addresses
            for n, address in enumerate(addr_list):
                numAddresses += 1
                num = len(wallet.get_address_history(address))
                is_used = wallet.is_used(address)
                balance = sum(wallet.get_addr_balance(address))
                address_text = address.to_ui_string()
                label = wallet.labels.get(address.to_storage_string(), '')
                balance_text = self.parent.format_amount(balance, whitespaces=False)
                is_frozen = wallet.is_frozen(address)
                fiat_balance = (fx.value_str(balance, fx.exchange_rate()) + " " + fx.get_currency()) if fx else ""
                #Entry = "address addr_str addr_idx, label, balance_str, fiat_balance_str, num_tx, is_frozen, balance, is_change, is_used, base_unit"
                item = AddressData.Entry(address, address_text, n, label, balance_text, fiat_balance, num,
                                         bool(is_frozen), balance, bool(is_change), bool(is_used), base_unit)
                
                #_TYPES = ("Any","Receiving","Change")
                #_STATUSES = ("All", "Funded", "Unused", "Used")           
                self.master[0][0].append(item) # item belongs in 'Any,All' regardless
                self.master[2 if item.is_change else 1][0].append(item) # append to either change or receiving of 'All' list
                if item.balance:
                    self.master[0][1].append(item) # item belongs in 'Any,Funded' regardless
                    self.master[2 if item.is_change else 1][1].append(item) # append to either change or receiving of 'Funded' list
                if item.num_tx:
                    self.master[0][3].append(item) # item belongs in the 'Any,Used' always, if used
                    self.master[2 if item.is_change else 1][3].append(item) # append to either change or receiving of 'All' list
                else: # Unused list
                    self.master[0][2].append(item) # item belongs in the 'Any,Unused' always, if unused
                    self.master[2 if item.is_change else 1][2].append(item) # append to either change or receiving of 'All' list
        
        # sort addresses by balance, num_tx, and index, descending
        for i,l1 in enumerate(self.master):
            for j,l2 in enumerate(l1):
                l2.sort(key=lambda x: [x.balance,x.num_tx,0-x.addr_idx], reverse=True )
                #print(_TYPES[i],_STATUSES[j],"len",len(l2))
        
        utils.NSLog("fetched %d addresses from wallet in %f ms",numAddresses,(time.time()-t0)*1e3)
    

def present_modal_address_picker(callback, vc = None) -> None:
    parent = gui.ElectrumGui.gui
    avc = AddressesVC.alloc().initWithMode_(ModePicker).autorelease()
    nav = utils.tintify(UINavigationController.alloc().initWithRootViewController_(avc).autorelease())
    def pickedAddress(entry) -> None:
        if callable(callback):
            callback(entry)
        nav.presentingViewController.dismissViewControllerAnimated_completion_(True, None)
    utils.add_callback(avc, 'on_picked', pickedAddress)
    parent.add_navigation_bar_close_to_modal_vc(avc, leftSide = True)
    if vc is None: vc = parent.get_presented_viewcontroller()
    vc.presentViewController_animated_completion_(nav, True, None)

def EntryForAddress(address : str) -> object:
    address = str(address)
    address = Address.from_string(address)
    addrData = _Get()
    if not addrData: return
    try:
        l = addrData.master[0][0]
        for entry in l:
            if str(entry.address) == str(address):
                return entry
    except:
        print("Exception in EntryForAddress:",str(sys.exc_info()[1]))
        
    return None

def PushDetail(address_or_entry : object, navController : ObjCInstance) -> ObjCInstance:
    entry = None
    if isinstance(address_or_entry, (str,Address)): entry = EntryForAddress(str(address_or_entry))
    elif isinstance(address_or_entry, AddressData.Entry):
        entry = address_or_entry
    if not entry:
        raise ValueError('PushDetailForAddress -- missing entry for address!')
    addrDetail = AddressDetail.alloc().init().autorelease()
    utils.nspy_put_byname(addrDetail, entry, 'entry')
    navController.pushViewController_animated_(addrDetail, True)
    return addrDetail

from typing import Any
class AddressesMgr(utils.DataMgr):
    def doReloadForKey(self, key : Any) -> Any:
        a = AddressData(gui.ElectrumGui.gui)
        a.refresh()
        utils.NSLog("AddressMgr refresh")
        return a

def _Get() -> AddressData:
    return gui.ElectrumGui.gui.sigAddresses.get(None)

def _GetBBTitle(x = None) -> Any:
    if x is not None:
        return [ _("Show CashAddr"), _("Show Legacy") ]
    if gui.ElectrumGui.gui.prefs_get_use_cashaddr():
        return _("Show Legacy")
    return _("Show CashAddr")

def _ShowAddressContextMenu(entry, parentvc, ipadAnchor, toggleFreezeCallback = None):
    parent = gui.ElectrumGui.gui
    if not parent.wallet:
        utils.NSLog("_ShowAddressContextMenu: wallet is None -- possibly backgrounded/closed wallet. Returning early.")
        return
    def on_block_explorer() -> None:
        parent.view_on_block_explorer(entry.address, 'addr')
    def on_request_payment() -> None:
        parent.jump_to_receive_with_address(entry.address)
    def on_private_key() -> None:
        def onPw(password : str) -> None:
            # present the private key view controller here.
            pk = None
            try:
                pk = parent.wallet.export_private_key(entry.address, password) if parent.wallet else None
            except:
                parent.show_error(str(sys.exc_info()[1]))
                return
            if pk:
                vc = private_key_dialog.PrivateKeyDialog.alloc().init().autorelease()
                pkentry = private_key_dialog.PrivateKeyEntry(entry.address, pk, entry.is_frozen, entry.is_change)
                utils.nspy_put_byname(vc, pkentry, 'entry')
                parentvc.navigationController.pushViewController_animated_(vc, True)
        parent.prompt_password_if_needed_asynch(onPw)
    def on_sign_verify() -> None:
        vc = sign_decrypt_dialog.Create_SignVerify_VC(entry.address)
        parentvc.navigationController.pushViewController_animated_(vc, True)

    def on_encrypt_decrypt() -> None:
        if not parent.wallet: return
        try:
            pubkey = parent.wallet.get_public_key(entry.address)
        except:
            print("exception extracting public key:",str(sys.exc_info()[1]))
            return
        if pubkey is not None and not isinstance(pubkey, str):
            pubkey = pubkey.to_ui_string()
        if not pubkey:
            return
        vc = sign_decrypt_dialog.Create_EncryptDecrypt_VC(entry.address, pubkey)
        parentvc.navigationController.pushViewController_animated_(vc, True)
    
    def on_copy() -> None:
        UIPasteboard.generalPasteboard.string = entry.addr_str
        utils.show_notification(message=_("Address copied to clipboard"))

    actions = [
            [ _('Cancel') ],
            [ _('Copy Address'), on_copy ],
            #[ _('Show as QR code'), lambda: parentvc.onQRBut() ],
            [ _("View on block explorer"), on_block_explorer ],
            [ _("Request payment"), on_request_payment ],
        ]
    
    watch_only = False if parent.wallet and not parent.wallet.is_watching_only() else True

    if not watch_only:
        def onToggleFreeze() -> None:
            _ToggleFreeze(entry)
            if callable(toggleFreezeCallback):
                toggleFreezeCallback()
        actions.append([ _('Freeze') if not entry.is_frozen else _('Unfreeze'), onToggleFreeze ])

    if not watch_only and not entry.is_frozen and entry.balance > 0:
        actions.append([ _('Spend from this Address'), lambda: _SpendFrom(entry, vc = parentvc) ] )

    if not watch_only:
        actions.append([ _('Private key'), on_private_key ] )
        
    if not watch_only and entry.address.kind == entry.address.ADDR_P2PKH:
        actions.append([ _('Sign/verify Message'), on_sign_verify ] )
        actions.append([ _('Encrypt/decrypt Message'), on_encrypt_decrypt ] )
        
    utils.show_alert(
        vc = parentvc,
        title = _("Options"),
        message = entry.addr_str,#[0:12] + "..." + entry.addr_str[-12:],
        actions = actions,
        cancel = _('Cancel'),
        style = UIAlertControllerStyleActionSheet,
        ipadAnchor = ipadAnchor
    )

def _ToggleFreeze(entry):
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        parent.wallet.set_frozen_state([entry.address], not entry.is_frozen)
        parent.wallet.storage.write()
        parent.refresh_components('addresses')

def _SpendFrom(entry, vc = None):
    parent = gui.ElectrumGui.gui
    if parent.wallet:
        coins = parent.wallet.get_spendable_coins([entry.address], parent.config)
        if coins:
            parent.jump_to_send_with_spend_from(coins, vc = vc)
