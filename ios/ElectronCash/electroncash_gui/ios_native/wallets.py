from . import utils
from . import gui
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

class WalletsNav(WalletsNavBase):
   
    @objc_method
    def dealloc(self) -> None:
        send_super(__class__, self, 'dealloc')

class WalletsVC(WalletsVCBase):

    @objc_method
    def dealloc(self) -> None:
        # cleanup code here..
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
            self.statusLabel.text = _("Downloading Headers")
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
        iv.image = self.bluchk
        old = tv.cellForRowAtIndexPath_(NSIndexPath.indexPathForRow_inSection_(self.selectedRow,indexPath.section))
        if old:
            iv = old.viewWithTag_(1)
            iv.image = None
        self.selectedRow = indexPath.row            
        
class WalletsTxsHelper(WalletsTxsHelperBase):
        
    @objc_method
    def dealloc(self) -> None:
        #cleanup code here
        send_super(__class__, self, 'dealloc')
     
    @objc_method 
    def miscSetup(self) -> None:
        #nib = UINib.nibWithNibName_bundle_("TODO", None)
        #self.tv.registerNib_forCellReuseIdentifier_(nib, "TODO")
        pass
        
       
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        # TODO: Implement this properly
        return 1


    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath) -> ObjCInstance:
        identifier = "Cell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            cell =  UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
        cell.textLabel.text = _("No transactions")
        cell.detailTextLabel.text = _("No transactions for this wallet exist on the blockchain.")
        return cell

    #@objc_method
    #def tableView_heightForRowAtIndexPath_(self, tv : ObjCInstance, indexPath : ObjCInstance) -> float:
    #    return 86.0

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
