from . import utils
from . import gui
from .txdetail import TxDetail
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *
from .custom_objc import *
from collections import namedtuple

HistoryEntry = namedtuple("HistoryEntry", "extra_data tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image")


class HistoryTableVC(UITableViewController):
    ''' History Tab -- shows tx's, etc

        Possible 'add_callback'-style callbacks:
    
           'on_change_compact_mode' -- get notified when the tableview goes from compact to expanded mode. Takes 1 bool arg.
    '''
    needsRefresh = objc_property()
    compact = objc_property()

    @objc_method
    def initWithStyle_(self, style : int):
        self = ObjCInstance(send_super(__class__, self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
        self.title = _("History")
        self.tabBarItem.image = UIImage.imageNamed_("tab_history.png").imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal)
        
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()

        self.navigationItem.rightBarButtonItem = UIBarButtonItem.alloc().init().autorelease()
        self.setCompactMode_(True)
        return self

    @objc_method
    def dealloc(self) -> None:
        self.needsRefresh = None
        self.compact = None
        utils.nspy_pop(self)
        send_super(__class__, self, 'dealloc')

    @objc_method
    def viewDidLoad(self) -> None:
        send_super(__class__, self, 'viewDidLoad')
        nib = UINib.nibWithNibName_bundle_("HistoryCellLarge", None)
        self.tableView.registerNib_forCellReuseIdentifier_(nib, "HistoryCellLarge")

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
        identifier = "HistoryCellCompact" if self.compact else "HistoryCellLarge"
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            if self.compact:
                cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
            else:
                cell = NSBundle.mainBundle.loadNibNamed_owner_options_("HistoryCellLarge",None,None)[0]
        try:
            history = utils.nspy_get_byname(self, 'history')
            if not history:
                cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, "NoTXs").autorelease()
                empty_cell(cell,_("No transactions"),True)
            else:
                entry = history[indexPath.row]
                if self.compact:
                    setup_cell_for_history_entry(cell, entry)
                else:
                    setup_large_cell_for_history_entry(cell, entry)
                    cell.descTf.delegate = self
                    cell.descTf.tag = indexPath.row
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
    def tableView_heightForRowAtIndexPath_(self, tv, indexPath) -> float:
        if not self.compact:
            return 130.0
        return 44.0
   
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
            
    @objc_method
    def toggleCompactMode(self) -> None:
        self.setCompactMode_(not self.compact)
        
    @objc_method
    def setCompactMode_(self, b : bool) -> None:
        if self.compact is not None and b == bool(self.compact):
            return
        self.compact = b
        #self.navigationItem.rightBarButtonItem.title = _("Expand") if b else _("Compactify")
        #self.navigationItem.rightBarButtonItem.possibleTitles = NSSet.setWithArray_([ _("Compactify"), _("Expand") ])
        self.navigationItem.rightBarButtonItem.image = UIImage.imageNamed_("but_expand_v.png") if b else UIImage.imageNamed_("but_compact_v.png")
        self.navigationItem.rightBarButtonItem.target = self
        self.navigationItem.rightBarButtonItem.action = SEL(b'toggleCompactMode')
        self.navigationItem.rightBarButtonItem.style = UIBarButtonItemStylePlain
        if self.viewIfLoaded:
            self.tableView.reloadData()
        utils.get_callback(self, 'on_change_compact_mode')(b)
        
    @objc_method
    def textFieldShouldReturn_(self, tf) -> bool:
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidEndEditing_(self, tf) -> None:
        history = utils.nspy_get_byname(self, 'history')
        if not history or tf.tag < 0 or tf.tag >= len(history):
            utils.NSLog("ERROR -- Label text field unknown tag: %d",int(tf.tag))
            return
        entry = history[tf.tag]
        newLabel = tf.text
        if newLabel != entry.label:
            gui.ElectrumGui.gui.on_label_edited(entry.tx_hash, newLabel)
        
        
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

def setup_large_cell_for_history_entry(cell : ObjCInstance, entry : object) -> None:
    if not isinstance(cell, HistoryCellLarge):
        empty_cell(cell)
        return
    dummy1, tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, val, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img, *dummy2 = entry

    ff = str(date)
    if conf > 0:
        ff = "%s %s"%(conf, language.gettext('confirmations'))
    if label is None:
        label = ''
        
    lblColor = UIColor.blackColor if val >= 0 else UIColor.colorWithRed_green_blue_alpha_(153.0/255.0,51.0/255.0,51.0/255.0,1.0) #"#993333"
    #bgColor = UIColor.colorWithRed_green_blue_alpha_(0.91746425629999995,0.95870447160000005,0.99979293349999998,1.0) if val >= 0 else UIColor.colorWithRed_green_blue_alpha_(0.99270844459999996,0.96421206000000004,0.99976575369999998,1.0)
    bgColor = cell.bal.backgroundColor if val >= 0 else UIColor.colorWithRed_green_blue_alpha_(0.99270844459999996,0.96421206000000004,0.99976575369999998,1.0)
    
    cell.status1.text = status_str
    cell.descTf.placeholder = _("Description")
    cell.descTf.text = label
    #cell.descTf.backgroundColor = bgColor
    cell.descTf.textColor = lblColor
    cell.status2.text = ff
    cell.amt.text = v_str + (("(" + fiat_amount_str + " " + ccy + ") ") if fiat_amount else '')
    cell.amt.textColor = lblColor
    cell.amt.backgroundColor = bgColor
    cell.bal.text = balance_str + (("(" + fiat_balance_str + " " + ccy + ") ") if fiat_balance else '')

    #cell.amt.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    #cell.bal.font = UIFont.monospacedDigitSystemFontOfSize_weight_(17.0, UIFontWeightRegular)
    
    cell.icon.image = img
    cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
       

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
    if isinstance(cell, HistoryCellLarge):
        cell.bal.text = ''
        cell.amt.text = ''
        cell.descTf.text = txt
        cell.status1.text = txt
        cell.status2.text = ''
        cell.tag = -1
        cell.icon.image = None
    else:        
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