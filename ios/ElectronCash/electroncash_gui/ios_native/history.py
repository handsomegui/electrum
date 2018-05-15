from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language

import time, math, sys
from collections import namedtuple

from .uikit_bindings import *
from .custom_objc import *

HistoryEntry = namedtuple("HistoryEntry", "tx tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image")
#######################################################################
# HELPER STUFF EXPORTED TO OTHER MODULES ('Addresses' uses these too) #
#######################################################################
StatusImages = [  # Indexed by 'status' from tx info and/or HistoryEntry
    UIImage.imageNamed_("warning.png").retain(),
    UIImage.imageNamed_("warning.png").retain(),
    UIImage.imageNamed_("unconfirmed.png").retain(),
    UIImage.imageNamed_("unconfirmed.png").retain(),
    UIImage.imageNamed_("clock1.png").retain(),
    UIImage.imageNamed_("clock2.png").retain(),
    UIImage.imageNamed_("clock3.png").retain(),
    UIImage.imageNamed_("clock4.png").retain(),
    UIImage.imageNamed_("clock5.png").retain(),
    UIImage.imageNamed_("grnchk.png").retain(),
    UIImage.imageNamed_("signed.png").retain(),
    UIImage.imageNamed_("unsigned.png").retain(),
]

from . import txdetail

def get_history(domain : list = None, statusImagesOverride : list = None, forceNoFX : bool = False) -> list:
    ''' For a given set of addresses (or None for all addresses), builds a list of
        HistoryEntry '''
    sImages = StatusImages if not statusImagesOverride or len(statusImagesOverride) < len(StatusImages) else statusImagesOverride
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    daemon = parent.daemon
    if wallet is None or daemon is None:
        utils.NSLog("get_history: wallent and/or daemon was None, returning early")
        return None
    h = wallet.get_history(domain)
    fx = daemon.fx if daemon.fx and daemon.fx.show_history() else None
    history = list()
    ccy = ''
    for h_item in h:
        tx_hash, height, conf, timestamp, value, balance = h_item
        status, status_str = wallet.get_tx_status(tx_hash, height, conf, timestamp)
        has_invoice = wallet.invoices.paid.get(tx_hash)
        v_str = parent.format_amount(value, True, whitespaces=True)
        balance_str = parent.format_amount(balance, whitespaces=True)
        label = wallet.get_label(tx_hash)
        date = timestamp_to_datetime(time.time() if conf <= 0 else timestamp)
        ts = timestamp if conf > 0 else time.time()
        fiat_amount = fiat_balance = 0
        fiat_amount_str = fiat_balance_str = ''
        if fx: fx.history_used_spot = False
        if not forceNoFX and fx:
            if not ccy:
                ccy = fx.get_currency()
            try:
                hdate = timestamp_to_datetime(time.time() if conf <= 0 else timestamp)
                hamount = fx.historical_value(value, hdate)
                htext = fx.historical_value_str(value, hdate) if hamount else ''
                fiat_amount = hamount if hamount else fiat_amount
                fiat_amount_str = htext if htext else fiat_amount_str
                hamount = fx.historical_value(balance, hdate) if balance else 0
                htext = fx.historical_value_str(balance, hdate) if hamount else ''
                fiat_balance = hamount if hamount else fiat_balance
                fiat_balance_str = htext if htext else fiat_balance_str
            except:
                utils.NSLog("Exception in get_history computing fiat amounts!\n%s",str(sys.exc_info()[1]))
                #import traceback
                #traceback.print_exc(file=sys.stderr)
                fiat_amount = fiat_balance = 0
                fiat_amount_str = fiat_balance_str = ''
        if status >= 0 and status < len(sImages):
            img = sImages[status]
        else:
            img = None
        entry = HistoryEntry('', tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, value, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img)
        history.append(entry) # appending is O(1)
    history.reverse() # finally, reverse the order to keep most recent first
    utils.NSLog("history: retrieved %d entries",len(history))
    return history

from typing import Any

class HistoryMgr(utils.DataMgr):
    def doReloadForKey(self, key : Any) -> Any:
        hist = get_history(domain = key)
        utils.NSLog("HistoryMgr refresh for domain: %s", str(key))
        return hist

_tx_cell_height = 76.0 # TxHistoryCell height in points
_kern = -0.5 # kerning for some of the text labels in the view in points
_f1 = UIFont.systemFontOfSize_weight_(16.0,UIFontWeightBold).retain()
_f2 = UIFont.systemFontOfSize_weight_(11.0,UIFontWeightBold).retain()
_f3 = UIFont.systemFontOfSize_weight_(1.0,UIFontWeightThin).retain()
_s3 = ns_from_py(' ').sizeWithAttributes_({NSFontAttributeName:_f3})
_date_width = None

class TxHistoryHelper(TxHistoryHelperBase):
    haveShowMoreTxs = objc_property()

    @objc_method
    def dealloc(self) -> None:
        #cleanup code here
        print("TxHistoryHelper dealloc")
        gui.ElectrumGui.gui.sigHistory.disconnect(self.ptr.value)
        try:
            domain = _GetDomain(self)
            if domain is not None:
                gui.ElectrumGui.gui.historyMgr.unsubscribe(domain)
        except: utils.NSLog("TxHistoryHelper: Could not remove self from historyMgr domain!\n%s",str(sys.exc_info()[1]))
        self.haveShowMoreTxs = None
        utils.nspy_pop(self) # clear 'txs' python dict
        send_super(__class__, self, 'dealloc')
     
    @objc_method 
    def miscSetup(self) -> None:
        nib = UINib.nibWithNibName_bundle_("TxHistoryCell", None)
        self.tv.registerNib_forCellReuseIdentifier_(nib, "TxHistoryCell")
        try:
            domain = _GetDomain(self)
            if domain is not None:
                gui.ElectrumGui.gui.historyMgr.subscribe(domain)
        except: utils.NSLog("TxHistoryHelper: Could not add self to historyMgr domain!:\n%s",str(sys.exc_info()[1]))
        self.tv.refreshControl = gui.ElectrumGui.gui.helper.createAndBindRefreshControl()
        def gotRefresh() -> None:
            if self.tv:
                if self.tv.refreshControl: self.tv.refreshControl.endRefreshing()
                self.tv.reloadData()
        gui.ElectrumGui.gui.sigHistory.connect(gotRefresh, self.ptr.value)
       
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        # TODO: Implement this properly
        h = _GetTxs(self)
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
            helper = NewTxHistoryHelper(tv = vc.view, vc = self.vc, domain = _GetDomain(self))
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
        h = _GetTxs(self)
        if not h:
            identifier = "Cell"
            cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
            if cell is None:
                cell =  UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            cell.textLabel.text = _("No transactions")
            cell.detailTextLabel.text = _("No transactions for this wallet exist on the blockchain.")
            return cell            
        identifier = "TxHistoryCell"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("TxHistoryCell",None,None)
            for obj in objs:
                if isinstance(obj, UITableViewCell) and obj.reuseIdentifier == identifier:
                    cell = obj
                    break
        global _date_width
        if _date_width is None:
            _date_width = cell.dateWidthCS.constant
        #HistoryEntry = tx tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image
        entry = h[indexPath.row]
        ff = '' #str(entry.date)
        if entry.conf and entry.conf > 0 and entry.conf < 6:
            ff = "%s %s"%(entry.conf, _('confirmations'))

        cell.amountTit.setText_withKerning_(_("Amount"), _kern)
        cell.balanceTit.setText_withKerning_(_("Balance"), _kern)
        cell.statusTit.setText_withKerning_(_("Status"), _kern)
        def strp(s : str) -> str:
            return s.translate({ord(i):None for i in '+- '}) #strip +/-
        cell.amount.text = strp(entry.v_str)
        cell.balance.text = strp(entry.balance_str)
        '''
        # begin experimental fiat history rates zone
        cell.amount.numberOfLines = 0
        cell.balance.numberOfLines = 0
        cell.dateWidthCS.constant = _date_width
        def nsattrstring(amtStr, fiatStr, ccy, pad) -> ObjCInstance:
            #print("str=",amtStr,"pad=",pad,"spacesize=",s3.width)
            p = ''
            if fiatStr and not self.compactMode:
                if pad > 0.0:
                    n = round(pad / _s3.width)
                    p = ''.join([' ' for i in range(0, n)])
                fiatStr = p + '  ' +  fiatStr + ' ' + ccy
            else:
                fiatStr = ''
            ats = NSMutableAttributedString.alloc().initWithString_(amtStr + fiatStr).autorelease()
            ats.addAttribute_value_range_(NSFontAttributeName,_f1,NSRange(0,len(amtStr)))
            if fiatStr:
                cell.dateWidthCS.constant = _date_width - 24.0
                r0 = NSRange(len(amtStr),len(p))
                ats.addAttribute_value_range_(NSFontAttributeName,_f3,r0)
                r = NSRange(len(amtStr)+len(p),len(fiatStr)-len(p))
                r2 = NSRange(ats.length()-(len(ccy)+1),len(ccy))
                ats.addAttribute_value_range_(NSFontAttributeName,_f2,r)
                ats.addAttribute_value_range_(NSKernAttributeName,_kern*1.25,r)
                #ats.addAttribute_value_range_(NSBaselineOffsetAttributeName,3.0,r)
                ats.addAttribute_value_range_(NSForegroundColorAttributeName,cell.amountTit.textColor,r)
                #ats.addAttribute_value_range_(NSFontAttributeName,_f3,r2)
                #ats.addAttribute_value_range_(NSObliquenessAttributeName,0.1,r)
                ps = NSMutableParagraphStyle.new().autorelease()
                ps.setParagraphStyle_(NSParagraphStyle.defaultParagraphStyle)
                ps.alignment = NSJustifiedTextAlignment
                #ps.lineBreakMode = NSLineBreakByWordWrapping
                ats.addAttribute_value_range_(NSParagraphStyleAttributeName, ps, r)
            return ats
        amtStr = strp(entry.v_str)
        balStr = strp(entry.balance_str)
        s1 = ns_from_py(amtStr).sizeWithAttributes_({NSFontAttributeName:_f1})
        s2 = ns_from_py(balStr).sizeWithAttributes_({NSFontAttributeName:_f1})
        cell.amount.attributedText = nsattrstring(amtStr,strp(entry.fiat_amount_str),entry.ccy,s2.width-s1.width) 
        cell.balance.attributedText = nsattrstring(balStr,strp(entry.fiat_balance_str),entry.ccy,s1.width-s2.width)
        # end experimental zone...
        '''
        cell.desc.setText_withKerning_(entry.label.strip() if isinstance(entry.label, str) else '', _kern)
        cell.icon.image = UIImage.imageNamed_("tx_send.png") if entry.value and entry.value < 0 else UIImage.imageNamed_("tx_recv.png")
        cell.date.text = entry.status_str
        cell.status.text = ff #if entry.conf < 6 else ""
        cell.statusIcon.image = entry.status_image
        
        return cell

    @objc_method
    def tableView_heightForRowAtIndexPath_(self, tv : ObjCInstance, indexPath : ObjCInstance) -> float:
        return _tx_cell_height if indexPath.row > 0 or _GetTxs(self) else 44.0

    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        tv.deselectRowAtIndexPath_animated_(indexPath,True)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        if not self.vc:
            utils.NSLog("TxHistoryHelper: No self.vc defined, cannot proceed to tx detail screen")
            return
        try:
            entry = _GetTxs(self)[indexPath.row]
        except:
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        if tx is None:
            raise Exception("Wallets: Could not find Transaction for tx '%s'"%str(entry.tx_hash))
        txd = txdetail.CreateTxDetailWithEntry(entry,tx=tx)        
        self.vc.navigationController.pushViewController_animated_(txd, True)

def NewTxHistoryHelper(tv : ObjCInstance, vc : ObjCInstance, domain : list = None, noRefreshControl = False) -> ObjCInstance:
    helper = TxHistoryHelper.new().autorelease()
    tv.dataSource = helper
    tv.delegate = helper
    helper.tv = tv
    helper.vc = vc
    # optimization to share the same history data with the new helper class we just created for the full mode view
    # .. hopefully this will keep the UI peppy and responsive!
    if domain is not None:
        utils.nspy_put_byname(helper, domain, 'domain')
    helper.miscSetup()
    if noRefreshControl: helper.tv.refreshControl = None
    from rubicon.objc.runtime import libobjc            
    libobjc.objc_setAssociatedObject(tv.ptr, helper.ptr, helper.ptr, 0x301)
    return helper

# this should be a method of TxHistoryHelper but it returns a python object, so it has to be a standalone global function
def _GetTxs(txsHelper : object) -> list:
    if not txsHelper:
        raise ValueError('GetTxs: Need to specify a TxHistoryHelper instance')
    h = gui.ElectrumGui.gui.historyMgr.get(_GetDomain(txsHelper))
    return h

def _GetDomain(txsHelper : object) -> list:
    if not txsHelper:
        raise ValueError('GetDomain: Need to specify a TxHistoryHelper instance')
    return utils.nspy_get_byname(txsHelper, 'domain')    