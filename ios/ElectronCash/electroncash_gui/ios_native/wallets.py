from . import utils
from . import gui
from . import history
from electroncash.i18n import _, language

from .uikit_bindings import *
from .custom_objc import *

# from ViewsForIB.h, WalletsStatusMode enum
StatusOffline = 0
StatusOnline = 1
StatusDownloadingHeaders = 2
StatusSynchronizing = 3


StatusColors = {
    StatusOnline : UIColor.colorWithRed_green_blue_alpha_(187.0/255.0,255.0/255.0,59.0/255.0,1.0).retain(),
    StatusOffline : UIColor.colorWithRed_green_blue_alpha_(255.0/255.0,97.0/255.0,97.0/255.0,1.0).retain(),
    StatusDownloadingHeaders : UIColor.colorWithRed_green_blue_alpha_(255.0/255.0,194.0/255.0,104.0/255.0,1.0).retain(),
    StatusSynchronizing : UIColor.colorWithRed_green_blue_alpha_(104.0/255.0,255.0/255.0,179.0/255.0,1.0).retain(),
}

VChevronImages = [
    UIImage.imageNamed_("chevron_00000").retain(),
    UIImage.imageNamed_("chevron_00001").retain(),
    UIImage.imageNamed_("chevron_00002").retain(),
    UIImage.imageNamed_("chevron_00003").retain(),
    UIImage.imageNamed_("chevron_00004").retain(),
    UIImage.imageNamed_("chevron_00005").retain(),
]

class WalletsNav(WalletsNavBase):    
    @objc_method
    def dealloc(self) -> None:
        send_super(__class__, self, 'dealloc')

class WalletsVC(WalletsVCBase):
    lineHider = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here..
        gui.ElectrumGui.gui.sigHistory.disconnect(self.ptr.value)
        gui.ElectrumGui.gui.sigRequests.disconnect(self.ptr.value)

        self.lineHider = None
        send_super(__class__, self, 'dealloc')  

    @objc_method
    def commonInit(self) -> None:
        # put additional setup code here
        self.status = StatusOffline # re-does the text/copy and colors
        self.walletAmount.text = "0"
        # Custom Segmented Control setup
        self.segControl.items = [_("Transactions"), _("Requests")]
        self.segControl.showsCount = False
        cols = [65.0/255.0, 204.0/255.0]
        self.segControl.setTitleColor_forState_(UIColor.colorWithWhite_alpha_(cols[0], 1.0),UIControlStateSelected)
        self.segControl.setTitleColor_forState_(UIColor.colorWithWhite_alpha_(cols[1], 1.0),UIControlStateNormal)
        self.segControl.font = UIFont.systemFontOfSize_weight_(16.0, UIFontWeightSemibold)
        self.segControl.autoAdjustSelectionIndicatorWidth = False
        # Can't set this property from IB, so we do it here programmatically to create the stroke around the receive button
        self.receiveBut.layer.borderColor = self.sendBut.backgroundColor.CGColor

        gui.ElectrumGui.gui.sigHistory.connect(lambda: self.doChkTableViewCounts(), self.ptr.value)
        gui.ElectrumGui.gui.sigRequests.connect(lambda: self.doChkTableViewCounts(), self.ptr.value)
    
    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        self.commonInit()
        self.drawerHelper.miscSetup()
        self.txsHelper.miscSetup()

    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        f = self.navBar.frame
        # This line hider is a hack/fix for a weirdness in iOS where there is a white line between the top nav bar and the bottom
        # 'drawer' area.  This hopefully fixes that.
        self.lineHider = UIView.alloc().initWithFrame_(CGRectMake(0,f.size.height,f.size.width,1)).autorelease()
        self.lineHider.backgroundColor = self.blueBarTop.backgroundColor
        self.navBar.addSubview_(self.lineHider)
        self.lineHider.autoresizingMask = (1<<6)-1
        self.doChkTableViewCounts()

    @objc_method
    def viewWillDisappear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillDisappear:', animated, argtypes=[c_bool])
        if self.lineHider:
            self.lineHider.removeFromSuperview()
            self.lineHider = None

    @objc_method
    def viewLayoutMarginsDidChange(self) -> None:
        send_super(__class__, self, 'viewLayoutMarginsDidChange')
        if self.txsHelper and self.txsHelper.tv:
            self.txsHelper.tv.reloadData() # this implicitly redoes the central table and the number of preview transactions we see in it
            self.doChkTableViewCounts()

    @objc_method
    def showRefreshControl(self):
        if self.txsHelper.tv and self.txsHelper.tv.refreshControl is not None and not self.txsHelper.tv.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            tv = self.txsHelper.tv
            rc = self.txsHelper.tv.refreshControl
            rc.beginRefreshing()
            tv.setContentOffset_animated_(CGPointMake(0, tv.contentOffset.y-rc.frame.size.height), True)

    @objc_method
    def setStatus_(self, mode : int) -> None:
        send_super(__class__, self, 'setStatus:', mode, argtypes=[c_int])
        if self.viewIfLoaded is None or self.statusLabel is None:
            utils.NSLog("WARNING: WalletsVC setStatus on a WalletsVC that is not fully initialized!")
            return
        c = None
        try:
            c = StatusColors[mode]
        except:
            c = StatusColors[StatusOffline]
        self.statusLabel.backgroundColor = c
        if mode == StatusOnline:
            self.statusBlurb.text = _("All set and good to go.")
            self.statusLabel.text = _("Online")
        elif mode == StatusDownloadingHeaders:
            self.statusBlurb.text = _("Transaction history may not yet be current.")
            self.statusLabel.text = " " + _("Downloading Headers") + "   " # hack -- pad with spaces so it look right.. TODO: fix this issue
        elif mode == StatusSynchronizing:
            self.statusBlurb.text = _("Updating transaction history.")
            self.statusLabel.text = _("Synchronizing")
        else: # mode == StatusOffline        
            self.statusBlurb.text = _("Cannot send/receive new transactions.")
            self.statusLabel.text = _("Offline")
            
        self.statusBlurb.sizeToFit()

    @objc_method
    def toggleDrawer(self) -> None:
        if self.drawerHelper.isOpen:
            self.drawerHelper.closeAnimated_(True)
        else:
            self.drawerHelper.openAnimated_(True)

    @objc_method
    def addWallet(self) -> None:
        if self.addWalletView.hasAnimations:
            print("addWalletView animation already active, ignoring spurious second tap....")
            return
        c = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.0,0.10)
        def doAddWallet() -> None:
            gui.ElectrumGui.gui.show_message(message="'Add Wallet' is not yet implemented.", title="Coming Soon!")
        self.addWalletView.backgroundColorAnimationToColor_duration_reverses_completion_(c,0.2,True,doAddWallet)
        
    @objc_method
    def didChangeSegment_(self, control : ObjCInstance) -> None:
        ix = self.segControl.selectedSegmentIndex
        if ix == 0:
            self.txsHelper.tv.setHidden_(False)
            self.reqstv.setHidden_(True)
        elif ix == 1:
            self.txsHelper.tv.setHidden_(True)
            self.reqstv.setHidden_(False)
            self.reqstv.reloadData()
        self.doChkTableViewCounts()

    # Detects if a tap was in the status label or on the status blurb
    @objc_method
    def gestureRecognizerShouldBegin_(self, gr : ObjCInstance) -> bool:
        s = self.statusLabel.bounds.size
        s2 = self.statusBlurb.bounds.size
        p = gr.locationInView_(self.statusLabel)
        p2 = gr.locationInView_(self.statusBlurb)
        return self.navigationController.visibleViewController.ptr.value == self.ptr.value and \
                ( (p.x >= 0 and p.y >= 0 and p.x <= s.width and p.y <= s.height) \
                  or (p2.x >= 0 and p2.y >= 0 and p2.x <= s2.width and p2.y <= s2.height) )
                  

    # pops up the network setup dialog and also does a little animation on the status label
    @objc_method
    def onTopNavTap(self) -> None:
        if self.statusLabel.hasAnimations:
            print("status label animation already active, ignoring spurious second tap....")
            return
        c1 = self.statusLabel.backgroundColor.colorWithAlphaComponent_(0.50)
        c2 = self.statusBlurb.textColor.colorWithAlphaComponent_(0.10)
        def doShowNetworkDialog() -> None:
            gui.ElectrumGui.gui.show_network_dialog()
        self.statusLabel.backgroundColorAnimationToColor_duration_reverses_completion_(c1,0.2,True,doShowNetworkDialog)
        self.statusBlurb.textColorAnimationToColor_duration_reverses_completion_(c2,0.2,True,None)
        
    @objc_method
    def onSendBut(self) -> None:
        gui.ElectrumGui.gui.show_send_modal()

    @objc_method
    def onReceiveBut(self) -> None:
        gui.ElectrumGui.gui.show_receive_modal()
        
    @objc_method
    def doChkTableViewCounts(self) -> None:
        if not self.reqstv or not self.txsHelper or not self.txsHelper.tv or not self.segControl or not self.reqstv.dataSource:
            return
        if self.segControl.selectedSegmentIndex == 0:
            # Transactions
            ntx = self.txsHelper.tableView_numberOfRowsInSection_(self.txsHelper.tv, 0)
            self.noTXsView.setHidden_(bool(ntx))
            self.noReqsView.setHidden_(True)
            self.txsHelper.tv.setHidden_(not bool(ntx))
        elif self.segControl.selectedSegmentIndex == 1:
            # Requests
            nreq = self.reqstv.dataSource.tableView_numberOfRowsInSection_(self.reqstv, 0)
            self.noTXsView.setHidden_(True)
            self.noReqsView.setHidden_(bool(nreq))
            self.reqstv.setHidden_(not bool(nreq))


class WalletsDrawerHelper(WalletsDrawerHelperBase):
    selectedRow = objc_property()
    bluchk = objc_property()
        
    @objc_method
    def dealloc(self) -> None:
        #cleanup code here
        self.selectedRow = None
        self.bluchk = None
        send_super(__class__, self, 'dealloc')
     
    @objc_method 
    def miscSetup(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsMisc",None,None)
        for obj in objs:
            if isinstance(obj, UIView) and obj.tag == 2000:
                self.tv.tableFooterView = obj
                self.vc.addWalletView = obj
        for obj in objs:
            if isinstance(obj, UIGestureRecognizer) and obj.view and self.vc.addWalletView \
                   and obj.view.ptr.value == self.vc.addWalletView.ptr.value:
                obj.addTarget_action_(self.vc, SEL(b'addWallet'))
        nib = UINib.nibWithNibName_bundle_("WalletsDrawerCell", None)
        self.tv.registerNib_forCellReuseIdentifier_(nib, "WalletsDrawerCell")

        
       
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        # TODO: Implement this properly
        return 2

    @objc_method
    def tableView_heightForHeaderInSection_(self, tableView, section) -> float:
        return 22.0

    @objc_method
    def tableView_viewForHeaderInSection_(self, tableView, section) -> ObjCInstance:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsMisc",None,None)
        for obj in objs:
            if isinstance(obj, UIView) and obj.tag == 1000:
                name = obj.viewWithTag_(1)
                size = obj.viewWithTag_(2)
                name.setText_withKerning_(_("Name"), utils._kern) 
                size.setText_withKerning_(_("Size:").translate({ord(i):None for i in ':'}), utils._kern)
                return obj
        return None

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath) -> ObjCInstance:
        identifier = "WalletsDrawerCell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsDrawerCell",None,None)
            for obj in objs:
                if isinstance(obj, UITableViewCell) and obj.reuseIdentifier == identifier:
                    cell = obj
                    break
        iv = cell.viewWithTag_(1)
        name = cell.viewWithTag_(2)
        size = cell.viewWithTag_(3)
        if not self.bluchk:
            self.bluchk = iv.image
        if indexPath.row is not self.selectedRow:
            iv.image = None
        else:
            iv.image = self.bluchk
        name.text = "Wallet %d"%int(indexPath.row+1)
        size.text = str(pow(2,indexPath.row+4)) + " KB"
        return cell

    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv : ObjCInstance, indexPath : ObjCInstance) -> float:
        return 60.0

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
        n = self.tableView_numberOfRowsInSection_(tv,0)
        cell = tv.cellForRowAtIndexPath_(indexPath)
        iv = cell.viewWithTag_(1)
        old = tv.cellForRowAtIndexPath_(NSIndexPath.indexPathForRow_inSection_(self.selectedRow,indexPath.section))
        if old: old.viewWithTag_(1).image = None
        iv.image = self.bluchk
        self.selectedRow = indexPath.row
        
    # overrides base
    @objc_method
    def openAnimated_(self, animated : bool) -> None:
        self.chevron.animationImages = VChevronImages
        if not self.chevron.isAnimating() and animated:
            self.chevron.animationDuration = 0.2
            self.chevron.animationRepeatCount = 1
            self.chevron.startAnimating()
        else:
            self.chevron.stopAnimating()
        self.chevron.image = VChevronImages[-1]
        #self.isOpen = True
        send_super(__class__, self, 'openAnimated:', animated, argtypes=[c_bool])

    # overrides base
    @objc_method
    def closeAnimated_(self, animated : bool) -> None:
        self.chevron.animationImages = list(reversed(VChevronImages))
        if not self.chevron.isAnimating() and animated:
            self.chevron.animationDuration = 0.2
            self.chevron.animationRepeatCount = 1
            self.chevron.startAnimating()
        else:
            self.chevron.stopAnimating()
        self.chevron.image = VChevronImages[0]
        #self.isOpen = False
        send_super(__class__, self, 'closeAnimated:', animated, argtypes=[c_bool])