from . import utils
from . import gui
from . import history
from . import txdetail
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

StatusImages = history.statusImages.copy()
StatusImages[9] = UIImage.imageNamed_("grnchk.png").retain()

class WalletsNav(WalletsNavBase):
   
    @objc_method
    def dealloc(self) -> None:
        send_super(__class__, self, 'dealloc')

class WalletsVC(WalletsVCBase):
    needsRefresh = objc_property()

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here..
        self.needsRefresh = None
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
    
    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        self.commonInit()
        self.drawerHelper.miscSetup()
        self.txsHelper.miscSetup()

    @objc_method
    def updateHistoryFromWallet(self):
        h = history.get_history(statusImagesOverride = StatusImages, forceNoFX = True)
        if h is None:
            # probable backgroundeed and/or wallet is closed
            return
        utils.nspy_put_byname(self, h, 'history')
        utils.NSLog("Wallets: fetched %d entries from history",len(h))

    @objc_method
    def refresh(self):
        self.updateHistoryFromWallet()
        if self.txsHelper.tv:
            if self.txsHelper.tv.refreshControl: self.txsHelper.tv.refreshControl.endRefreshing()
            self.txsHelper.tv.reloadData()
        self.needsRefresh = False

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
        c1 = UIColor.whiteColor
        c2 = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.0,0.10)
        def doAddWallet() -> None:
            gui.ElectrumGui.gui.show_message(message="'Add Wallet' is not yet implemented.", title="Coming Soon!")
        self.addWalletView.backgroundColorAnimationFromColor_toColor_duration_reverses_completion_(c1,c2,0.2,True,doAddWallet)
        
    @objc_method
    def didChangeSegment_(self, control : ObjCInstance) -> None:
        print("Did change segment", self.segControl.selectedSegmentIndex)
        
    @objc_method
    def onSendBut(self) -> None:
        print("Send button clicked, todo: IMPLEMENT")

    @objc_method
    def onReceiveBut(self) -> None:
        print("Receive button clicked, todo: IMPLEMENT")


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
            elif isinstance(obj, UIGestureRecognizer):
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
                name.text = _("Name") + ":"
                size.text = _("Size:")
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
        
class WalletsTxsHelper(WalletsTxsHelperBase):
        
    @objc_method
    def dealloc(self) -> None:
        #cleanup code here
        send_super(__class__, self, 'dealloc')
     
    @objc_method 
    def miscSetup(self) -> None:
        nib = UINib.nibWithNibName_bundle_("WalletsHistoryCell", None)
        self.tv.registerNib_forCellReuseIdentifier_(nib, "WalletsHistoryCell")
       
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        # TODO: Implement this properly
        h = GetHistory(self.vc)
        return 1 if not h else len(h)


    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath) -> ObjCInstance:
        h = GetHistory(self.vc)
        if not h:
            identifier = "Cell"
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            if cell is None:
                cell =  UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            cell.textLabel.text = _("No transactions")
            cell.detailTextLabel.text = _("No transactions for this wallet exist on the blockchain.")
            return cell            
        identifier = "WalletsHistoryCell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsHistoryCell",None,None)
            for obj in objs:
                if isinstance(obj, UITableViewCell) and obj.reuseIdentifier == identifier:
                    cell = obj
                    break
        #HistoryEntry = tx tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image
        entry = h[indexPath.row]
        ff = '' #str(entry.date)
        if entry.conf and entry.conf > 0 and entry.conf < 6:
            ff = "%s %s"%(entry.conf, _('confirmations'))

        cell.amountTit.text = _("Amount")
        cell.balanceTit.text = _("Balance")
        cell.statusTit.text = _("Status")
        cell.amount.text = entry.v_str.translate({ord(i):None for i in '+- '}) #strip +/-
        cell.balance.text = entry.balance_str.translate({ord(i):None for i in '+- '}) # strip +/- from amount
        cell.desc.text = entry.label.strip() if isinstance(entry.label, str) else ''
        cell.icon.image = UIImage.imageNamed_("tx_send.png") if entry.value and entry.value < 0 else UIImage.imageNamed_("tx_recv.png")
        cell.date.text = entry.status_str
        cell.status.text = ff #if entry.conf < 6 else ""
        cell.statusIcon.image = entry.status_image
        
        return cell

    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv : ObjCInstance, indexPath : ObjCInstance) -> float:
        return 86.0 if indexPath.row > 0 or GetHistory(self.vc) else 44.0

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = GetHistory(self.vc)[indexPath.row]
        except:
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        if tx is None:
            raise Exception("Wallets: Could not find Transaction for tx '%s'"%str(entry.tx_hash))
        txd = txdetail.CreateTxDetailWithEntry(entry,tx=tx)        
        self.vc.navigationController.pushViewController_animated_(txd, True)

def GetHistory(vc):
    h = utils.nspy_get_byname(vc, 'history')
    if h is None:
        vc.updateHistoryFromWallet()
        h = utils.nspy_get_byname(vc, 'history')            
    return h
