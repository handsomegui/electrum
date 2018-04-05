from . import utils
from . import gui
from .txdetail import TxDetail
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *
from collections import namedtuple

HistoryEntry = namedtuple("HistoryEntry", "extra_data tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image")


# History Tab -- shows tx's, etc
class HistoryTableVC(UITableViewController):
    needsRefresh = objc_property()

    @objc_method
    def initWithStyle_(self, style : int):
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
        self.title = _("History")
        self.tabBarItem.image = UIImage.imageNamed_("tab_history.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
        
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()

        return self

    @objc_method
    def dealloc(self) -> None:
        self.needsRefresh = None
        utils.nspy_pop(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 1

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        try:
            history = utils.nspy_get_byname(self, 'history')
            return len(history) if history else 1
        except:
            print("Error, no history")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        identifier = "%s_%s"%(str(__class__) , str(indexPath.section))
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
        try:
            history = utils.nspy_get_byname(self, 'history')
            if not history:
                empty_cell(cell,_("No transactions"),True)
            else:
                entry = history[indexPath.row]
                setup_cell_for_history_entry(cell, entry)
        except Exception as e:
            print("exception in tableView_cellForRowAtIndexPath_: %s"%str(e))
            empty_cell(cell)
        return cell
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR ROW %d"%indexPath.row)
        parent = gui.ElectrumGui.gui
        if parent.wallet is None:
            return
        try:
            entry = utils.nspy_get_byname(self, 'history')[indexPath.row]
        except:
            tv.deselectRowAtIndexPath_animated_(indexPath,True)
            return        
        tx = parent.wallet.transactions.get(entry.tx_hash, None)
        rawtx = None
        if tx is not None: rawtx = tx.raw
        txd = TxDetail.alloc()
        utils.nspy_put_byname(txd, entry, 'tx_entry')
        self.navigationController.pushViewController_animated_(txd.initWithRawTx_(rawtx).autorelease(), True)
    
    @objc_method
    def updateHistoryFromWallet(self):
        history = get_history()
        if history is None:
            # probable backgroundeed and/or wallet is closed
            return
        utils.nspy_put_byname(self, history, 'history')
        print ("fetched %d entries from history"%len(history))

    @objc_method
    def refresh(self):
        self.updateHistoryFromWallet()
        if self.refreshControl: self.refreshControl.endRefreshing()
        if self.tableView:
            self.tableView.reloadData()
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
        if self.refreshControl is not None and not self.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            self.refreshControl.beginRefreshing()
            self.tableView.setContentOffset_animated_(CGPointMake(0, self.tableView.contentOffset.y-self.refreshControl.frame.size.height), True)

#######################################################################
# HELPER STUFF EXPORTED TO OTHER MODULES ('Addresses' uses these too) #
#######################################################################
statusImages = [  # Indexed by 'status' from tx info and/or HistoryEntry
    UIImage.imageNamed_("warning.png").retain(),
    UIImage.imageNamed_("warning.png").retain(),
    UIImage.imageNamed_("unconfirmed.png").retain(),
    UIImage.imageNamed_("unconfirmed.png").retain(),
    UIImage.imageNamed_("clock1.png").retain(),
    UIImage.imageNamed_("clock2.png").retain(),
    UIImage.imageNamed_("clock3.png").retain(),
    UIImage.imageNamed_("clock4.png").retain(),
    UIImage.imageNamed_("clock5.png").retain(),
    UIImage.imageNamed_("confirmed.png").retain(),
]

def setup_cell_for_history_entry(cell : ObjCInstance, entry : object) -> None:
    dummy1, tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, val, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img, *dummy2 = entry

    ff = str(date)
    if conf > 0:
        ff = "%s %s"%(conf, language.gettext('confirmations'))
    if label is None:
        label = ''
    lblColor = "#000000" if val >= 0 else "#993333"
    lblSep = ' - ' if len(label) else ''
    title = utils.nsattributedstring_from_html(('<font face="system font,arial,helvetica,verdana" size=2>%s</font>'
                                               + '<font face="system font,arial,helvetica,verdana" size=4>%s<font color="%s"><b>%s</b></font></font>')
                                               %(html.escape(status_str),
                                                 lblSep,
                                                 lblColor,
                                                 ''+html.escape(label)+'' if len(label)>0 else ''
                                                 ))
    pstyle = NSMutableParagraphStyle.alloc().init().autorelease()
    pstyle.lineBreakMode = NSLineBreakByTruncatingTail
    title.addAttribute_value_range_(NSParagraphStyleAttributeName, pstyle, NSRange(0,title.length()))
    detail = utils.nsattributedstring_from_html(('<p align="justify" style="font-family:system font,arial,helvetica,verdana">'
                                                + 'Amt: <font face="monaco, menlo, courier" color="%s"><strong>%s%s</strong></font>'
                                                + ' - Bal: <font face="monaco, menlo, courier"><strong>%s%s</strong></font>'
                                                + ' - <font size=-1 color="#666666"><i>(%s)</i></font>'
                                                + '</p>')
                                                %(lblColor,html.escape(v_str),
                                                  (("(" + fiat_amount_str + " " + ccy + ") ") if fiat_amount else ''),
                                                  html.escape(balance_str),
                                                  (("(" + fiat_balance_str + " " + ccy + ") ") if fiat_balance else ''),
                                                  html.escape(ff)))
    detail.addAttribute_value_range_(NSParagraphStyleAttributeName, pstyle, NSRange(0,detail.length()))
    cell.imageView.image = img
    cell.textLabel.text = None
    cell.textLabel.adjustsFontSizeToFitWidth = False if len(label) > 0 else True
    cell.textLabel.lineBreakMode = NSLineBreakByTruncatingTail# if len(label) > 0 else NSLineBreakByClipping
    cell.textLabel.numberOfLines = 1 #if len(label) <= 0 else 2
    cell.textLabel.attributedText = title
    cell.textLabel.updateConstraintsIfNeeded()
    cell.detailTextLabel.text = None
    cell.detailTextLabel.adjustsFontSizeToFitWidth = False
    cell.detailTextLabel.lineBreakMode = NSLineBreakByTruncatingTail
    cell.detailTextLabel.numberOfLines = 1
    cell.detailTextLabel.attributedText = detail
    cell.detailTextLabel.updateConstraintsIfNeeded()
    cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator

def get_history(domain : list = None) -> list:
    ''' For a given set of addresses (or None for all addresses), builds a list of
        HistoryEntry '''
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
        if fx:
            if not ccy:
                ccy = fx.get_currency()
            hdate = timestamp_to_datetime(time.time() if conf <= 0 else timestamp)
            hamount = fx.historical_value(value, hdate)
            htext = fx.historical_value_str(value, hdate) if hamount else ''
            fiat_amount = hamount if hamount else fiat_amount
            fiat_amount_str = htext if htext else fiat_amount_str
            hamount = fx.historical_value(balance, hdate)
            htext = fx.historical_value_str(balance, hdate) if hamount else ''
            fiat_balance = hamount if hamount else fiat_balance
            fiat_balance_str = htext if htext else fiat_balance_str
        if status >= 0 and status < len(statusImages):
            img = statusImages[status]
        else:
            img = None
        entry = HistoryEntry('', tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, value, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img)
        history.insert(0,entry) # reverse order
    return history

def empty_cell(cell : ObjCInstance, txt : str = "*Error*", italic : bool = False) -> ObjCInstance:
    cell.textLabel.attributedText = None
    cell.textLabel.text = txt
    if italic:
        cell.textLabel.font = UIFont.italicSystemFontOfSize_(cell.textLabel.font.pointSize)
    else:
        cell.textLabel.font = UIFont.systemFontOfSize_(cell.textLabel.font.pointSize)
    cell.detailTextLabel.attributedText = None
    cell.detailTextLabel.text = None
    cell.accessoryType = UITableViewCellAccessoryNone
    return cell