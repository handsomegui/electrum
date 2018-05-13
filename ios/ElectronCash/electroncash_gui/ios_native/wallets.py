from . import utils
from . import gui
from . import history
from . import txdetail
from electroncash.i18n import _, language

from .uikit_bindings import *
from .custom_objc import *
import math

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

StatusImages = history.statusImages.copy()
StatusImages[9] = UIImage.imageNamed_("grnchk.png").retain()

VChevronImages = [
    UIImage.imageNamed_("chevron_00000").retain(),
    UIImage.imageNamed_("chevron_00001").retain(),
    UIImage.imageNamed_("chevron_00002").retain(),
    UIImage.imageNamed_("chevron_00003").retain(),
    UIImage.imageNamed_("chevron_00004").retain(),
    UIImage.imageNamed_("chevron_00005").retain(),
]

VC = None

_kern = -0.5 # kerning for some of the text labels in the view in points
_tx_cell_height = 76.0 # WalletsTxCell height in points

class WalletsNav(WalletsNavBase):    
    @objc_method
    def dealloc(self) -> None:
        send_super(__class__, self, 'dealloc')

class WalletsVC(WalletsVCBase):
    needsRefresh = objc_property()
    reqsLoadedAtLeastOnce = objc_property()
    lineHider = objc_property()
    allTxHelpers = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here..
        global VC
        if VC and VC.ptr.value == self.ptr.value:
            VC = None
        self.needsRefresh = None
        self.reqsLoadedAtLeastOnce = None
        self.lineHider = None
        self.allTxHelpers = None
        send_super(__class__, self, 'dealloc')  

    @objc_method
    def commonInit(self) -> None:
        global VC
        if not VC: VC = self
        self.allTxHelpers = NSMutableArray.new().autorelease()
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
        self.refresh() # this implicitly redoes the central table and the number of preview transactions we see in it

    @objc_method
    def refresh(self):
        l = list(self.allTxHelpers)
        hdict = dict()
        ctr = 0
        for ptrval in l:
            txsHelper = ObjCInstance(objc_id(ptrval))
            if txsHelper:
                dlist = utils.nspy_get_byname(txsHelper, 'domain')
                domain = ''
                if isinstance(dlist, list): 
                    for d in dlist: domain += str(d)
                domain = None if not domain else domain
                h = hdict.get(domain, None)
                if h is None:
                    txsHelper.loadTxsFromWallet()
                    h = utils.nspy_get_byname(txsHelper, 'txs')
                    hdict[domain] = h
                else:
                    # avoid redundant loads of the same data.. reuse the same history data for child txsHelper views
                    utils.nspy_put_byname(txsHelper, h, 'txs')
                    ctr += 1
                if txsHelper.tv:
                    if txsHelper.tv.refreshControl: txsHelper.tv.refreshControl.endRefreshing()
                    txsHelper.tv.reloadData()
                self.needsRefresh = False
        if ctr > 0:
            utils.NSLog("Wallets: re-used history data for %d child tableviews.",ctr)
        self.doChkTableViewCounts()


    @objc_method
    def refreshReqs(self):
        if not self.reqstv: return
        self.reqstv.reloadData() # HACK TODO FIXME: create a real helper class to manage this
        if self.reqstv.refreshControl: self.reqstv.refreshControl.endRefreshing()
        self.doChkTableViewCounts()

    @objc_method
    def needUpdate(self):
        if self.needsRefresh: return
        self.needsRefresh = True
        self.retain()
        def inMain() -> None:
            self.doRefreshIfNeeded()
            self.autorelease()
        utils.do_in_main_thread(inMain)

    # This method runs in the main thread as it's enqueue using our hacky "Heartbeat" mechanism/workaround for iOS
    @objc_method
    def doRefreshIfNeeded(self):
        if self.needsRefresh:
            self.refresh()
            #print ("HISTORY REFRESHED")

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
            if not self.reqsLoadedAtLeastOnce:
                gui.ElectrumGui.gui.refresh_components('requests')
                self.reqsLoadedAtLeastOnce = True
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
                name.setText_withKerning_(_("Name"), _kern) 
                size.setText_withKerning_(_("Size:").translate({ord(i):None for i in ':'}), _kern)
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
        
        
class WalletsTxsHelper(WalletsTxsHelperBase):
    haveShowMoreTxs = objc_property()

    @objc_method
    def dealloc(self) -> None:
        #cleanup code here
        print("WalletsTxsHelper dealloc")
        try:
            theVC = self.vc
            if not isinstance(theVC, WalletsVC):
                theVC = VC
            theVC.allTxHelpers.removeObject_(self.ptr.value)
        except: utils.NSLog("WalletsTxsHelper: Could not remove self from vc.allTxHelpers")
        self.haveShowMoreTxs = None
        utils.nspy_pop(self) # clear 'txs' python dict
        send_super(__class__, self, 'dealloc')
     
    @objc_method 
    def miscSetup(self) -> None:
        nib = UINib.nibWithNibName_bundle_("WalletsTxCell", None)
        self.tv.registerNib_forCellReuseIdentifier_(nib, "WalletsTxCell")
        try:
            theVC = self.vc
            if not isinstance(theVC, WalletsVC):
                theVC = VC
            theVC.allTxHelpers.addObject_(self.ptr.value)
        except: utils.NSLog("WalletsTxsHelper: Could not add self to vc.allTxHelpers")
        self.tv.refreshControl = gui.ElectrumGui.gui.helper.createAndBindRefreshControl()
       
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        # TODO: Implement this properly
        h = GetTxs(self)
        rows = 0
        self.haveShowMoreTxs = False
        len_h = len(h) if h else 0
        if not self.compactMode:
            rows = len_h
        else:
            rows = max(math.floor(tableView.bounds.size.height / _tx_cell_height), 1)
            rows = min(rows,len_h)
            self.haveShowMoreTxs = len_h > rows
        return rows

    @objc_method
    def tableView_viewForFooterInSection_(self, tv, section : int) -> ObjCInstance:
        if self.haveShowMoreTxs:
            v = None
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsMisc",None,None)
            for o in objs:
                if not v and isinstance(o,UIView) and o.tag == 3000:
                    v = o
                    l = v.viewWithTag_(1)
                    if l: l.text = _("Show All Transactions")
            for o in objs:
                if isinstance(o, UIGestureRecognizer) and o.view and v \
                       and o.view.ptr.value == v.ptr.value:
                    o.addTarget_action_(self, SEL(b'onSeeAllTxs:'))
            return v
        return UIView.alloc().initWithFrame_(CGRectMake(0,0,0,0)).autorelease()

    @objc_method
    def onSeeAllTxs_(self, gr : ObjCInstance) -> None:
        if gr.view.hasAnimations:
            print("onSeeAllTxs: animation already active, ignoring spurious second tap....")
            return
        def seeAllTxs() -> None:
            # Push a new viewcontroller that contains just a tableview.. we create another instance of this
            # class to manage the tableview and set it up properly.  This should be fast as we are sharing tx history
            # data with the child instance via our "nspy_put" mechanism.
            vc = UIViewController.new().autorelease()
            vc.title = _("All Transactions")
            vc.view = UITableView.alloc().initWithFrame_style_(self.vc.view.frame, UITableViewStylePlain).autorelease()
            helper = NewWalletsTxsHelper(tv = vc.view, vc = self.vc, txs = GetTxs(self))
            self.vc.navigationController.pushViewController_animated_(vc, True)
        c = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.0,0.10)
        gr.view.backgroundColorAnimationToColor_duration_reverses_completion_(c,0.2,True,seeAllTxs)
 
    @objc_method
    def tableView_heightForFooterInSection_(self, tv, section : int) -> float:
        if self.compactMode:
            return 50.0
        return 0.0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath) -> ObjCInstance:
        h = GetTxs(self)
        if not h:
            identifier = "Cell"
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            if cell is None:
                cell =  UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            cell.textLabel.text = _("No transactions")
            cell.detailTextLabel.text = _("No transactions for this wallet exist on the blockchain.")
            return cell            
        identifier = "WalletsTxCell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsTxCell",None,None)
            for obj in objs:
                if isinstance(obj, UITableViewCell) and obj.reuseIdentifier == identifier:
                    cell = obj
                    break
        #HistoryEntry = tx tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image
        entry = h[indexPath.row]
        ff = '' #str(entry.date)
        if entry.conf and entry.conf > 0 and entry.conf < 6:
            ff = "%s %s"%(entry.conf, _('confirmations'))

        cell.amountTit.setText_withKerning_(_("Amount"), _kern)
        cell.balanceTit.setText_withKerning_(_("Balance"), _kern)
        cell.statusTit.setText_withKerning_(_("Status"), _kern)
        cell.amount.text = entry.v_str.translate({ord(i):None for i in '+- '}) #strip +/-
        cell.balance.text = entry.balance_str.translate({ord(i):None for i in '+- '}) # strip +/- from amount
        cell.desc.setText_withKerning_(entry.label.strip() if isinstance(entry.label, str) else '', _kern)
        cell.icon.image = UIImage.imageNamed_("tx_send.png") if entry.value and entry.value < 0 else UIImage.imageNamed_("tx_recv.png")
        cell.date.text = entry.status_str
        cell.status.text = ff #if entry.conf < 6 else ""
        cell.statusIcon.image = entry.status_image
        
        return cell

    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv : ObjCInstance, indexPath : ObjCInstance) -> float:
        return _tx_cell_height if indexPath.row > 0 or GetTxs(self) else 44.0

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        if not self.vc:
            utils.NSLog("WalletsTxsHelper: No self.vc defined, cannot proceed to tx detail screen")
            return
        try:
            entry = GetTxs(self)[indexPath.row]
        except:
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        if tx is None:
            raise Exception("Wallets: Could not find Transaction for tx '%s'"%str(entry.tx_hash))
        txd = txdetail.CreateTxDetailWithEntry(entry,tx=tx)        
        self.vc.navigationController.pushViewController_animated_(txd, True)

    @objc_method
    def loadTxsFromWallet(self) -> None:
        domain = utils.nspy_get_byname(self, 'domain') # optionally set the domain associateed with this class for address detail view...
        h = history.get_history(statusImagesOverride = StatusImages, domain = domain)
        if h is None:
            # probable backgroundeed and/or wallet is closed, so return early
            return
        utils.nspy_put_byname(self, h, 'txs')
        utils.NSLog("WalletsTxsHelper: fetched %d entries from history",len(h))

def NewWalletsTxsHelper(tv : ObjCInstance, vc : ObjCInstance, txs : list = None, noRefreshControl = False, domain : list = None) -> ObjCInstance:
    helper = WalletsTxsHelper.new().autorelease()
    tv.dataSource = helper
    tv.delegate = helper
    helper.tv = tv
    helper.vc = vc
    helper.miscSetup()
    if noRefreshControl: helper.tv.refreshControl = None
    # optimization to share the same history data with the new helper class we just created for the full mode view
    # .. hopefully this will keep the UI peppy and responsive!
    if txs is not None:    utils.nspy_put_byname(helper, txs, 'txs')
    if domain is not None: utils.nspy_put_byname(helper, domain, 'domain')
    from rubicon.objc.runtime import libobjc            
    libobjc.objc_setAssociatedObject(tv.ptr, helper.ptr, helper.ptr, 0x301)
    return helper

# this should be a method of WalletsTxsHelper but it returns a python object, so it has to be a standalone global function
def GetTxs(txsHelper = None):
    if not txsHelper and VC:
        txsHelper = VC.txsHelper
    if not txsHelper:
        raise ValueError('GetTxs: You specified no txsHelper instance and we could not find one already active in memory')
    h = utils.nspy_get_byname(txsHelper, 'txs')
    if h is None:
        txsHelper.loadTxsFromWallet()
        h = utils.nspy_get_byname(txsHelper, 'txs')            
    return h
