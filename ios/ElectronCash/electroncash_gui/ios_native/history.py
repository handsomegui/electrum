from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
from .uikit_bindings import *
from collections import namedtuple

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
        if not forceNoFX and fx:
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
        if status >= 0 and status < len(sImages):
            img = sImages[status]
        else:
            img = None
        entry = HistoryEntry('', tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, value, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img)
        history.insert(0,entry) # reverse order
    utils.NSLog("history: retrieved %d entries",len(history))
    return history

from typing import Any

class HistoryMgr(utils.DataMgr):
    def doReloadForKey(self, key : Any) -> Any:
        hist = get_history(domain = key)
        utils.NSLog("HistoryMgr refresh for domain: %s", str(key))
        return hist
