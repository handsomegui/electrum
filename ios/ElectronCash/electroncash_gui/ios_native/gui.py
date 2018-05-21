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

import sys
import traceback
import bz2
import base64
import time
import threading
from decimal import Decimal
from functools import partial
try:
    from .uikit_bindings import *
except Exception as e:
    sys.exit("Error: Could not import iOS libs: %s"%str(e))
from . import utils
from . import history
from . import addresses
from . import send
from . import receive
from . import prefs
from . import password_dialog
from . import seed_dialog
from . import network_dialog
from . import coins
from . import contacts
from . import wallets
from .custom_objc import *

from electroncash.i18n import _, set_language, languages
from electroncash.plugins import run_hook
from electroncash import WalletStorage, Wallet
from electroncash.address import Address
from electroncash.util import UserCancelled, print_error, format_satoshis, format_satoshis_plain, PrintError, InvalidPassword
import electroncash.web as web

class WalletFileNotFound(Exception):
    pass

# from electroncash.wallet import Abstract_Wallet

# a dummy hard coded wallet with a few tx's in its history for testing
# encrypted with password 'bchbch'
hardcoded_testing_wallet = bz2.decompress(base64.b64decode(b'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'))

class MyTabBarController(UITabBarController):
    
    didLayout = objc_property()
    
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self is not None: self.didLayout = False
        return self
    
    @objc_method
    def viewDidLayoutSubviews(self) -> None:
        self.didLayout = True
        send_super(__class__, self, 'viewDidLayoutSubviews')


class GuiHelper(NSObject):
    
    @objc_method
    def init(self):
        self = ObjCInstance(send_super(__class__, self, 'init'))
        ElectrumGui.gui.sigHelper.connect(lambda: self.doUpdate(), self.ptr.value)
        return self
    
    @objc_method
    def dealloc(self) -> None:
        ElectrumGui.gui.sigHelper.disconnect(self.ptr.value)
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def onTimer_(self, ignored):
        pass
    
    @objc_method
    def doUpdate(self):
        if ElectrumGui.gui is not None:
            ElectrumGui.gui.on_status_update()
                    
    @objc_method
    def onRefreshControl_(self, refreshControl : ObjCInstance) -> None:
        if ElectrumGui.gui is not None:
            ElectrumGui.gui.refresh_all()

    @objc_method
    def bindRefreshControl_(self, refreshControl: ObjCInstance) -> None:
        if (refreshControl is not None
            and refreshControl.actionsForTarget_forControlEvent_(self, UIControlEventValueChanged) is None):
            refreshControl.addTarget_action_forControlEvents_(self,SEL('onRefreshControl:'), UIControlEventValueChanged)
            
    @objc_method
    def createAndBindRefreshControl(self) -> ObjCInstance:
        rc = UIRefreshControl.alloc().init().autorelease()
        self.bindRefreshControl_(rc)
        return rc
            
    @objc_method
    def onModalClose_(self,but) -> None:
        if ElectrumGui.gui is not None:
            ElectrumGui.gui.on_modal_close(but)
        
    @objc_method
    def navigationController_willShowViewController_animated_(self, nav, vc, anim : bool) -> None:
        return
        
    @objc_method
    def tabBarController_didEndCustomizingViewControllers_changed_(self, tabController, viewControllers, changed : bool) -> None:
        return


# Manages the GUI. Part of the ElectronCash API so you can't rename this class easily.
class ElectrumGui(PrintError):

    gui = None

    def __init__(self, config, daemon, plugins):
        ElectrumGui.gui = self
        self.appName = 'Electron-Cash'
        self.appDomain = 'com.c3-soft.ElectronCash'
        self.set_language()
          
        # Signals mechanism for publishing data to interested components asynchronously -- see self.refresh_components()
        self.sigHelper = utils.PySig()
        self.sigHistory = history.HistoryMgr() # this DataMgr instance also caches history data
        self.sigAddresses = utils.PySig()
        self.sigPrefs = utils.PySig()
        self.sigRequests = receive.RequestsMgr()
        self.sigNetwork = utils.PySig()
        self.sigContacts = contacts.ContactsMgr()
        self.sigCoins = utils.PySig()
        
        #todo: support multiple wallets in 1 UI?
        self.config = config
        self.daemon = daemon
        self.plugins = plugins
        self.wallet = None
        self.window = None
        self.tabController = None
        self.rootVCs = None
        self.tabs = None
        self.sendVC = None
        self.sendNav = None
        self.receiveVC = None
        self.receiveNav = None
        self.addressesNav = None
        self.addressesVC = None
        self.coinsNav = None
        self.coinsVC = None
        self.contactsVC = None
        self.contactsNav = None
        self.walletsNav = None
        self.walletsVC = None
        
        self.prefsVC = None
        self.prefsNav = None
        self.networkVC = None
        self.networkNav = None
        
        self.decimal_point = config.get('decimal_point', 5)
        self.fee_unit = config.get('fee_unit', 0)
        self.num_zeros     = self.prefs_get_num_zeros()
        self.alias_info = None # TODO: IMPLEMENT alias stuff
        
        Address.show_cashaddr(self.prefs_get_use_cashaddr())
        
        self.cash_addr_sig = utils.PySig()

        self.tx_notifications = []
        self.helper = None
        self.helperTimer = None
        self.lowMemoryToken = None
        self.downloadingNotif = None
        self.downloadingNotif_view = None
        self.queued_ext_txn = None
        self.queued_refresh_components = set()
        self.queued_refresh_components_mut = threading.Lock()
        self.last_refresh = 0
                
        self.window = UIWindow.alloc().initWithFrame_(UIScreen.mainScreen.bounds)
        NSBundle.mainBundle.loadNibNamed_owner_options_("Splash2",self.window,None)        
        self.window.makeKeyAndVisible()
        utils.NSLog("GUI instance created, splash screen 2 presented")

    def createAndShowUI(self):
        self.helper = GuiHelper.alloc().init()
                
        self.tabController = MyTabBarController.alloc().init().autorelease()
        self.tabController.tabBar.tintColor = utils.uicolor_custom('nav')
        self.tabController.tabBar.setTranslucent_(False)
    
        self.addressesVC = adr = addresses.AddressesTableVC.alloc().initWithMode_(UITableViewStylePlain, addresses.ModeNormal).autorelease()
        self.helper.bindRefreshControl_(self.addressesVC.refreshControl)
        
        self.coinsVC = cns = coins.CoinsTableVC.alloc().initWithStyle_(UITableViewStylePlain).autorelease()
        self.helper.bindRefreshControl_(self.coinsVC.refreshControl)
                
        self.contactsVC = cntcts = contacts.ContactsVC.new().autorelease()
        self.prefsVC = prefs.PrefsVC.new().autorelease()

        self.helper.bindRefreshControl_(self.contactsVC.refreshControl)
  
        # Wallets tab
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("WalletsTab",None,None)
        for obj in objs:
            if isinstance(obj, wallets.WalletsNav):
                self.walletsNav = nav1 = obj
                self.walletsVC = self.walletsNav.topViewController
                self.walletsVC.reqstv.refreshControl = self.helper.createAndBindRefreshControl()
                break
        if not self.walletsNav:
            raise Exception('Wallets Nav is None!')

        self.addressesNav = nav2 = UINavigationController.alloc().initWithRootViewController_(adr).autorelease()
        self.coinsNav = nav3 = UINavigationController.alloc().initWithRootViewController_(cns).autorelease()
        self.contactsNav = nav4 = UINavigationController.alloc().initWithRootViewController_(cntcts).autorelease()
        self.prefsNav = nav5 = UINavigationController.alloc().initWithRootViewController_(self.prefsVC).autorelease()

        self.tabs = [utils.tintify(x) for x in [nav1, nav2, nav3, nav4, nav5]]
        self.rootVCs = dict()
        for i,nav in enumerate(self.tabs):
            vc = nav.viewControllers[0]
            nav.tabBarItem.tag = i
            nav.viewControllers[0].tabBarItem.tag = i
            self.rootVCs[nav.ptr.value] = vc

        self.tabController.viewControllers = self.tabs
        self.tabController.delegate = self.helper # just in case we need this for later UI stuff...
        
        self.helper.doUpdate()

        self.lowMemoryToken = NSNotificationCenter.defaultCenter.addObserverForName_object_queue_usingBlock_(
            UIApplicationDidReceiveMemoryWarningNotification,
            UIApplication.sharedApplication,
            None,
            Block(lambda: self.on_low_memory(), restype=None)
        ).retain()

        self.window.backgroundColor = UIColor.whiteColor
        self.window.rootViewController = self.tabController

        self.window.makeKeyAndVisible()                 
             
        utils.NSLog("UI Created Ok")

        self.register_network_callbacks()
        
        # the below call makes sure UI didn't miss any "update" events and forces all components to refresh
        utils.call_later(1.0, lambda: self.refresh_all())
                
        return True

    
    def register_network_callbacks(self):
        # network callbacks
        if self.daemon.network:
            self.daemon.network.register_callback(self.on_history, ['on_history'])
            self.daemon.network.register_callback(self.on_quotes, ['on_quotes'])
            interests = ['updated', 'new_transaction', 'status',
                         'banner', 'verified', 'fee', 'interfaces']
            # To avoid leaking references to "self" that prevent the
            # window from being GC-ed when closed, callbacks should be
            # methods of this class only, and specifically not be
            # partials, lambdas or methods of subobjects.  Hence...
            self.daemon.network.register_callback(self.on_network, interests)
            utils.NSLog("REGISTERED NETWORK CALLBACKS")

    def unregister_network_callbacks(self):
        if self.daemon and self.daemon.network:
            self.daemon.network.unregister_callback(self.on_history)
            self.daemon.network.unregister_callback(self.on_quotes)
            self.daemon.network.unregister_callback(self.on_network)
            utils.NSLog("UN-REGISTERED NETWORK CALLBACKS")
    
            
    def get_image_for_tab_index(self, index) -> ObjCInstance:
        if not self.tabController: return None
        vcs = self.tabController.viewControllers
        if index < 0 or index >= len(vcs): return None
        return vcs[index].tabBarItem.image
          
    def setup_downloading_notif(self):
        if self.downloadingNotif is not None: return
        self.downloadingNotif = CWStatusBarNotification.new()
        def OnTap() -> None:
            self.query_hide_downloading_notif()
            pass
        # NB: if I change the type it crashes sometimes on app startup due to bugs in this control.. perhaps? 
        self.downloadingNotif.notificationAnimationType = CWNotificationAnimationTypeOverlay
        self.downloadingNotif.notificationTappedBlock = OnTap
        if self.downloadingNotif_view is None:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ActivityStatusNotificationView",None,None)
            if objs is None or not len(objs):
                raise Exception("Could not load ActivityStatusNotificationView nib!")
            lbl = objs[0].viewWithTag_(2)
            if lbl is not None:
                lbl.text = _("Downloading blockchain headers...")
            self.downloadingNotif_view = objs[0].retain()
    
    def __del__(self):
        utils.NSLog("GUI instance __del__")
        self.dispose()
          
    def dispose(self):
        self.queued_ext_txn = None
        if self.window is None:
            return
        self.stop_daemon()
        if self.lowMemoryToken is not None:
            NSNotificationCenter.defaultCenter.removeObserver_(self.lowMemoryToken.autorelease())
            self.lowMemoryToken = None
        if self.downloadingNotif is not None:
            self.dismiss_downloading_notif()
        if self.downloadingNotif_view is not None:
            self.downloadingNotif_view.autorelease()
            self.downloadingNotif_view = None
        self.networkNav = None
        self.networkVC = None
        self.prefsVC = None
        self.prefsNav = None
        if self.helperTimer is not None:
            self.helperTimer.invalidate()
            self.helperTimer = None
        if self.tabController is not None: 
            self.tabController.viewControllers = None
        if self.sendNav: self.sendNav.release()
        if self.receiveNav: self.receiveNav.release()
        self.sendNav = None
        self.sendVC = None
        self.receiveVC = None
        self.receiveNav = None
        self.addressesNav = None
        self.addressesVC = None
        self.coinsVC = None
        self.coinsNav = None
        self.contactsNav = None
        self.contactsVC = None
        self.window.rootViewController = None
        self.tabController = None
        self.window.release()
        self.window = None
        self.rootVCs = None
        self.tabs = None
        if self.helper is not None: self.helper.release()
        self.helper = None
        self.cash_addr_sig.clear()
        
        self.sigHelper.clear()
        self.sigHistory.clear()
        self.sigAddresses.clear()
        self.sigPrefs.clear()
        self.sigRequests.clear()
        self.sigNetwork.clear()
        self.sigContacts.clear()
        self.sigCoins.clear()
            
    def on_rotated(self): # called by PythonAppDelegate after screen rotation
        #update status bar label width
                
        # on rotation sometimes the notif gets messed up.. so re-create it
        #if self.downloadingNotif is not None and self.is_downloading_notif_showing() and self.downloadingNotif_view is not None:
        #    self.dismiss_downloading_notif()
        #    self.show_downloading_notif()
        pass

    
    def init_network(self):
        # Show network dialog if config does not exist
        if self.daemon.network:
            if self.config.get('auto_connect') is None:
                #wizard = InstallWizard(self.config, self.app, self.plugins, None)
                #wizard.init_network(self.daemon.network)
                #wizard.terminate()
                print("NEED TO SHOW WIZARD HERE")
                pass
            
    def on_history(self, b):
        utils.NSLog("ON HISTORY (IsMainThread: %s)",str(NSThread.currentThread.isMainThread))
        assert self.walletsVC is not None
        self.refresh_components('history', 'helper')
        
    def on_quotes(self, event, *args):
        utils.NSLog("ON QUOTES (IsMainThread: %s)",str(NSThread.currentThread.isMainThread))
        #if self.daemon.fx.history_used_spot: #TODO: this is from qt gui.. figure out what this means.. does it help rate-limit?
        self.refresh_components('history', 'addresses', 'helper', 'requests')
            
    def on_network(self, event, *args):
        utils.NSLog("ON NETWORK: %s (IsMainThread: %s)",event,str(NSThread.currentThread.isMainThread))
        if not self.daemon:
            utils.NSLog("(Returning early.. daemon stopped)")
            return
        assert self.walletsVC is not None
        if event == 'updated':
            self.refresh_components('helper', 'network')
        elif event == 'new_transaction':
            self.tx_notifications.append(args[0])
            self.refresh_components('history', 'addresses', 'helper')
        elif event == 'banner':
            #todo: handle console stuff here
            pass
        elif event == 'status':
            #todo: handle status update here
            self.refresh_components('helper')
        elif event in ['verified']:
            self.refresh_components('history', 'addresses', 'helper')
        elif event == 'fee':
            # todo: handle fee stuff here
            pass
        elif event in ['interfaces']:
            self.refresh_components('network')
        else:
            self.print_error("unexpected network message:", event, args)

    def show_downloading_notif(self, txt = None):
        if self.prefs_get_downloading_notif_hidden():
            return
        if self.downloadingNotif is None:
            self.setup_downloading_notif()

        if txt is not None and type(txt) is str:
            lbl = self.downloadingNotif_view.viewWithTag_(2)
            if lbl is not None: lbl.text = txt

        activityIndicator = self.downloadingNotif_view.viewWithTag_(1)
        if not activityIndicator.animating:
            activityIndicator.animating = True

        if self.is_downloading_notif_showing():
            return

        def Completion() -> None:
            pass
        self.downloadingNotif_view.removeFromSuperview()
        self.downloadingNotif.displayNotificationWithView_completion_(
            self.downloadingNotif_view,
            Completion
        )
        
    def is_downloading_notif_showing(self):
        return (self.downloadingNotif.notificationIsShowing and
                not self.downloadingNotif.notificationIsDismissing)
            
    def dismiss_downloading_notif(self):
        if self.downloadingNotif is None: return
        if not self.is_downloading_notif_showing(): return
        dnf = self.downloadingNotif
        self.downloadingNotif = None
        def compl() -> None:
            #print("Dismiss completion")
            if (self.downloadingNotif_view is not None
                and dnf.customView is not None
                and self.downloadingNotif_view.isDescendantOfView_(dnf.customView)):
                activityIndicator = self.downloadingNotif_view.viewWithTag_(1)
                activityIndicator.animating = False # turn off animation to save CPU cycles
                self.downloadingNotif_view.removeFromSuperview()
            dnf.release()
        dnf.dismissNotificationWithCompletion_(compl)
            
    def on_status_update(self):
        utils.NSLog("ON STATUS UPDATE (IsMainThread: %s)",str(NSThread.currentThread.isMainThread))
        show_dl_pct = None
        
        if not self.wallet or not self.daemon:
            utils.NSLog("(Returning early.. wallet and/or daemon stopped)")
            self.walletVC.status = wallets.StatusOffline
            return
        
        walletStatus = wallets.StatusOffline
        walletBalanceTxt = ""
        walletUnitTxt = ""
        walletUnconfTxt = ""
        networkStatusText = _("Offline")
        icon = ""

        if self.daemon.network is None or not self.daemon.network.is_running():
            text = _("Offline")
            networkStatusText = text
            walletUnitTxt = text
            icon = "status_disconnected.png"

        elif self.daemon.network.is_connected():
            server_height = self.daemon.network.get_server_height()
            server_lag = self.daemon.network.get_local_height() - server_height
            # Server height can be 0 after switching to a new server
            # until we get a headers subscription request response.
            # Display the synchronizing message in that case.
            if not self.wallet.up_to_date or server_height == 0:
                text = _("Synchronizing...")
                networkStatusText = text
                walletUnitTxt = text
                icon = "status_waiting.png"
                walletStatus = wallets.StatusSynchronizing
            elif server_lag > 1:
                text = _("Server is lagging ({} blocks)").format(server_lag)
                walletUnitTxt = text
                networkStatusText = text
                icon = "status_lagging.png"
                walletStatus = wallets.StatusSynchronizing
            else:
                walletStatus = wallets.StatusOnline
                networkStatusText = _("Online")
                c, u, x = self.wallet.get_balance()
                walletBalanceTxt = self.format_amount(c)
                walletUnitTxt = self.base_unit()
                text =  _("Balance" ) + ": %s "%(self.format_amount_and_units(c))
                ux = 0
                if u:
                    s = " [%s unconfirmed]"%(self.format_amount(u, True).strip())
                    text +=  s
                    ux += u
                if x:
                    s = " [%s unmatured]"%(self.format_amount(x, True).strip())
                    text += s
                    ux += x
                if ux:
                    walletUnconfTxt += "[%s unconf.]"%(self.format_amount(ux, True)).strip()

                # append fiat balance and price
                if self.daemon.fx.is_enabled():
                    text += self.daemon.fx.get_fiat_status_text(c + u + x, self.base_unit(), self.get_decimal_point()) or ''
                    fiatAmtTxt = self.daemon.fx.format_amount_and_units(c)
                    walletUnitTxt += " (" + fiatAmtTxt + ")" if fiatAmtTxt and not u and not x else ''
                if not self.daemon.network.proxy:
                    icon = "status_connected.png"
                else:
                    icon = "status_connected_proxy.png"
            
            lh, sh = self.daemon.network.get_status_value('updated')        
            '''utils.NSLog("lh=%d sh=%d is_up_to_date=%d Wallet Network is_up_to_date=%d is_connecting=%d is_connected=%d",
                        int(lh), int(sh),
                        int(self.wallet.up_to_date),
                        int(self.daemon.network.is_up_to_date()),
                        int(self.daemon.network.is_connecting()),
                        int(self.daemon.network.is_connected()))
            '''
            if lh is not None and sh is not None and lh >= 0 and sh > 0 and lh < sh:
                show_dl_pct = int((lh*100.0)/float(sh))
                walletStatus = wallets.StatusDownloadingHeaders
                
        else:
            text = _("Not connected")
            walletUnitTxt = text
            icon = "status_disconnected.png"
            walletStatus = wallets.StatusOffline
            networkStatusText = _("Offline")


        lockIcon = "lock.png" if self.wallet and self.wallet.has_password() else "unlock.png"
        hasSeed =  bool(self.wallet.has_seed())

        if len(self.tx_notifications):
            self.notify_transactions()
            
        if show_dl_pct is not None and self.tabController.didLayout:
            self.show_downloading_notif(_("Downloading headers {}% ...").format(show_dl_pct) if show_dl_pct > 0 else None)
        else:
            self.dismiss_downloading_notif()
        
        self.walletsVC.status = walletStatus
        self.walletsVC.setAmount_andUnits_unconf_(walletBalanceTxt, walletUnitTxt, walletUnconfTxt)

        if self.prefsVC and (self.prefsVC.networkStatusText != networkStatusText
                             or self.prefsVC.lockIcon != lockIcon
                             or self.prefsVC.hasSeed != hasSeed):
            self.prefsVC.networkStatusText = networkStatusText
            self.prefsVC.networkStatusIcon = UIImage.imageNamed_(icon)
            self.prefsVC.lockIcon = lockIcon
            self.prefsVC.hasSeed = hasSeed
            self.prefsVC.refresh()
            
    def notify_transactions(self):
        if not self.daemon.network or not self.daemon.network.is_connected():
            return
        self.print_error("Notifying GUI")
        if len(self.tx_notifications) > 0:
            # Combine the transactions if there are at least 2
            num_txns = len(self.tx_notifications)
            if num_txns >= 2:
                total_amount = 0
                for tx in self.tx_notifications:
                    is_relevant, is_mine, v, fee = self.wallet.get_wallet_delta(tx)
                    if v > 0:
                        total_amount += v
                self.notify(_("{} new transactions received: Total amount received in the new transactions {}")
                            .format(num_txns, self.format_amount_and_units(total_amount)))
                self.tx_notifications = []
            else:
                for tx in self.tx_notifications:
                    if tx:
                        self.tx_notifications.remove(tx)
                        is_relevant, is_mine, v, fee = self.wallet.get_wallet_delta(tx)
                        if v > 0:
                            self.notify(_("New transaction received: {}").format(self.format_amount_and_units(v)))

    def notify(self, message):
        lines = message.split(': ')
        utils.show_notification(message=':\n'.join(lines),
                                duration=10.0,
                                color=(0.0, .5, .25, 1.0), # deeper green
                                textColor=UIColor.whiteColor,
                                font=UIFont.systemFontOfSize_(12.0),
                                style=CWNotificationStyleNavigationBarNotification,
                                multiline=bool(len(lines)))
        
    def query_hide_downloading_notif(self):
        vc = self.tabController if self.tabController.presentedViewController is None else self.tabController.presentedViewController
        utils.show_alert(vc = vc,
                         title = _("Hide Download Banner"),
                         message = _("Do you wish to hide the download progress banner?\n(You can re-enabled it in Settings later)"),
                         actions= [
                            [ _('Yes'), self.prefs_set_downloading_notif_hidden, True],
                            [ _('No') ],
                            ],
                         cancel = _('No')
                        )
        
            
    def get_root_vc(self, nav : ObjCInstance) -> ObjCInstance:
        if nav is None or not nav.ptr.value: return None
        ret = self.rootVCs.get(nav.ptr.value, None)
        if ret is None and isinstance(nav, UINavigationController) and len(nav.viewControllers):
            ret = nav.viewControllers[0]
        return ret

 
    def unimplemented(self, componentName : str) -> None:
        utils.show_timed_alert(self.get_presented_viewcontroller(),
                               "UNIMPLEMENTED", "%s unimplemented -- coming soon!"%(str(componentName)), 2.0)
   
            
    def on_modal_close(self, but : ObjCInstance) -> None:
        title = "UNKNOWN View Controller"
        try: 
            presented = self.tabController.presentedViewController
            title = py_from_ns(presented.visibleViewController.title)
        except:
            pass
        vc = self.tabController
        if but and but.tag:
            vc = ObjCInstance(objc_id(but.tag))
        vc.dismissViewControllerAnimated_completion_(True, None)
        
    def add_navigation_bar_close_to_modal_vc(self, vc : ObjCInstance, leftSide = True) -> ObjCInstance:
        closeButton = UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemStop, self.helper, SEL(b'onModalClose:')).autorelease()
        # poor man's weak ref -- used in above on_modal_close() to properly close nested modals
        closeButton.tag = vc.ptr.value
        if leftSide:
            extra = vc.navigationItem.leftBarButtonItems if vc.navigationItem.leftBarButtonItems else [] 
            vc.navigationItem.leftBarButtonItems = [closeButton, *extra]
        else:
            extra = vc.navigationItem.rightBarButtonItems if vc.navigationItem.rightBarButtonItems else [] 
            vc.navigationItem.rightBarButtonItems = [closeButton, *extra]
        return closeButton
        
        
    def cashaddr_icon(self):
        imgname = "addr_converter_bw.png"
        if self.prefs_get_use_cashaddr():
            imgname = "addr_converter.png"
        return UIImage.imageNamed_(imgname).imageWithRenderingMode_(UIImageRenderingModeAlwaysOriginal) 

    def toggle_cashaddr(self, on : bool) -> None:
        self.config.set_key('show_cashaddr', on)
        Address.show_cashaddr(on)
        self.refresh_all()
        self.cash_addr_sig.emit(on)
                  
    def format_amount(self, x, is_diff=False, whitespaces=False):
        return format_satoshis(x, is_diff, self.num_zeros, self.decimal_point, whitespaces)

    def format_amount_and_units(self, amount, usenl=False):
        text = self.format_amount(amount) + ' '+ self.base_unit()
        x = self.daemon.fx.format_amount_and_units(amount)
        if text and x:
            text += "\n" if usenl else ''
            text += ' (%s)'%x
        return text

    def format_fee_rate(self, fee_rate):
        if self.fee_unit == 0:
            return '{:.2f} sats/byte'.format(fee_rate/1000)
        else:
            return self.format_amount(fee_rate) + ' ' + self.base_unit() + '/kB'

    def base_unit(self):
        assert self.decimal_point in [2, 5, 8]
        if self.decimal_point == 2:
            return 'cash'
        if self.decimal_point == 5:
            return 'mBCH'
        if self.decimal_point == 8:
            return 'BCH'
        raise Exception('Unknown base unit')

    def get_decimal_point(self):
        return self.decimal_point
   
    def on_label_edited(self, key, newvalue):
        if self.wallet is None:
            return
        self.wallet.set_label(key, newvalue)
        self.wallet.storage.write()
        self.refresh_components("addresses", "history")


    def set_language(self):
        langs = NSLocale.preferredLanguages
        if langs:
            l = langs[0].replace('-','_')
            if not languages.get(l):
                # iOS sometimes returns a mixed language_REGION code, so try and match it to what we have 
                pre1 = l.split('_')[0]
                for k in languages.keys():
                    pre2 = k.split('_')[0]
                    if pre1 == pre2:
                        print("OS language is '%s', but we are guessing this matches our language code '%s'"%(l, k))
                        l = k
                        break
            print ("Setting language to {}".format(l))
            set_language(l)
            
    def prefs_set_downloading_notif_hidden(self, b : bool) -> None:
        was = self.prefs_get_downloading_notif_hidden()
        if b == was: return
        if b: self.dismiss_downloading_notif()
        self.config.set_key('hide_downloading_banner', bool(b))
        self.prefsVC.refresh()
        self.on_status_update()
    
    def prefs_get_downloading_notif_hidden(self) -> bool:
        return self.config.get('hide_downloading_banner', False)
        
    def prefs_get_show_fee(self) -> bool:
        return self.config.get('show_fee', True)
    
    def prefs_set_show_fee(self, b : bool) -> None:
        self.config.set_key('show_fee', bool(b))
        
    def prefs_get_max_fee_rate(self) -> float:
        return  float(format_satoshis_plain(self.config.max_fee_rate(), self.decimal_point))

    def prefs_set_max_fee_rate(self, r) -> float:
        amt = self.validate_amount(r)
        if amt is not None:
            self.config.set_key('max_fee_rate', amt)
        return self.prefs_get_max_fee_rate()
    
    def prefs_get_confirmed_only(self) -> bool:
        return bool(self.config.get('confirmed_only', False))
    
    def prefs_set_confirmed_only(self, b : bool) -> None:
        self.config.set_key('confirmed_only', bool(b))
        
    def prefs_get_use_change(self) -> tuple: # returns the setting plus a second bool that indicates whether this setting can be modified
        r1 = self.wallet.use_change
        r2 = self.config.is_modifiable('use_change')
        return r1, r2

    def prefs_set_use_change(self, x : bool) -> None:
        usechange_result = bool(x)
        if self.wallet.use_change != usechange_result:
            self.wallet.use_change = usechange_result
            self.wallet.storage.put('use_change', self.wallet.use_change)        
   
    def prefs_get_multiple_change(self) -> list:
        multiple_change = self.wallet.multiple_change
        enabled = self.wallet.use_change
        return multiple_change, enabled

    def prefs_set_multiple_change(self, x : bool) -> None:
        multiple = bool(x)
        if self.wallet.multiple_change != multiple:
            self.wallet.multiple_change = multiple
            self.wallet.storage.put('multiple_change', multiple)
    
    def prefs_get_use_cashaddr(self) -> bool:
        return bool(self.config.get('show_cashaddr', True))
    
    def prefs_set_decimal_point(self, dec: int) -> None:
        if dec in [2, 5, 8]:
            if dec == self.decimal_point:
                return
            self.decimal_point = dec
            self.config.set_key('decimal_point', self.decimal_point, True)
            self.refresh_all()
            print("Decimal point set to: %d"%dec)
        else:
            raise ValueError('Passed-in decimal point %s is not one of [2,5,8]'%str(dec))
        
    def prefs_get_num_zeros(self) -> int:
        return int(self.config.get('num_zeros', 2))
        
    def prefs_set_num_zeros(self, nz : int) -> None:
        value = int(nz)
        if self.num_zeros != value:
            self.num_zeros = value
            self.config.set_key('num_zeros', value, True)
            self.refresh_all()
            
    def view_on_block_explorer(self, item : str, which : str) -> None:
        which = which if which in ['tx', 'addr'] else None
        assert which is not None and item is not None
        url = web.BE_URL(self.config, which, item)
        if UIApplication.sharedApplication.respondsToSelector_(SEL(b'openURL:options:completionHandler:')):
            UIApplication.sharedApplication.openURL_options_completionHandler_(NSURL.URLWithString_(url),dict(),None)
        else:
            UIApplication.sharedApplication.openURL_(NSURL.URLWithString_(url))

    def validate_amount(self, text):
        try:
            x = Decimal(str(text))
        except:
            return None
        p = pow(10, self.decimal_point)
        return int( p * x ) if x > 0 else None
    
    def has_modal(self) -> ObjCInstance:
        rvc = self.window.rootViewController if self.window else None
        if rvc:
            return rvc.presentedViewController is not None
        return False
    
    def get_presented_viewcontroller(self) -> ObjCInstance:
        rvc = self.window.rootViewController if self.window else None
        pvc = rvc.presentedViewController if rvc is not None else None
        while pvc is not None and pvc.isBeingDismissed():
            # keep looking up the view controller hierarchy until we find a modal that is *NOT* being dismissed currently
            pvc = pvc.presentingViewController
        return rvc if pvc is None else pvc

    def get_current_nav_controller(self) -> ObjCInstance:
        return self.tabController.selectedViewController
    
    # can be called from any thread, always runs in main thread
    def show_error(self, message, title = _("Error"), onOk = None, localRunLoop = False, vc = None):
        return self.show_message(message=message, title=title, onOk=onOk, localRunLoop=localRunLoop, vc=vc)
    
    # full stop question for user -- appropriate for send tx dialog
    def question(self, message, title = _("Question"), yesno = False, onOk = None, vc = None, destructive = False, okButTitle = None) -> bool:
        ret = False
        localRunLoop = True if onOk is None else False
        def local_onOk() -> None:
            nonlocal ret
            ret = True
        okFun = local_onOk if localRunLoop else onOk
        extrakwargs = {}
        if yesno:
            extrakwargs = { 'cancelButTitle' : _("No"), 'okButTitle' : _("Yes") }
        if okButTitle:
            extrakwargs['okButTitle'] = okButTitle
        self.show_message(message=message, title=title, onOk=okFun, localRunLoop = localRunLoop, hasCancel = True, **extrakwargs, vc = vc, destructive = destructive)
        return ret
    
    # can be called from any thread, always runs in main thread
    def show_message(self, message, title = _("Information"), onOk = None, localRunLoop = False, hasCancel = False,
                     cancelButTitle = _('Cancel'), okButTitle = _('OK'), vc = None, destructive = False):
        def func() -> None:
            myvc = self.get_presented_viewcontroller() if vc is None else vc
            actions = [ [str(okButTitle)] ]
            if onOk is not None and callable(onOk): actions[0].append(onOk)
            if hasCancel:
                actions.append( [ str(cancelButTitle) ] )
            utils.show_alert(
                vc = myvc,
                title = title,
                message = message,
                actions = actions,
                localRunLoop = localRunLoop,
                cancel = cancelButTitle if hasCancel else None,
                destructive = str(okButTitle) if destructive else None,
            )
        if localRunLoop: return utils.do_in_main_thread_sync(func)
        return utils.do_in_main_thread(func)

    def delete_payment_request(self, addr : Address, refreshDelay : float = -1.0) -> bool:
        if self.wallet and self.wallet.remove_payment_request(addr, self.config):
            self.wallet.storage.write() # commit it to disk
            if refreshDelay <= 0.0:
                self.refresh_components('requests')
            else:
                utils.call_later(refreshDelay, lambda: self.refresh_components('requests'))
            return True
        return False

    def on_pr(self, request):
        #self.payment_request = request
        #if self.payment_request.verify(self.contacts):
        #    self.payment_request_ok_signal.emit()
        #else:
        #    self.payment_request_error_signal.emit()
        utils.NSLog("On PR: %s -- UNIMPLEMENTED.. IMPLEMENT ME!",str(request))
    
    def sign_payment_request(self, addr):
        ''' No-op for now -- needs to be IMPLEMENTED -- requires the alias functionality '''
        assert isinstance(addr, Address)
        if not self.wallet: return
        alias = self.config.get('alias')
        alias_privkey = None
        if alias and self.alias_info:
            alias_addr, alias_name, validated = self.alias_info
            if alias_addr:
                if self.wallet.is_mine(alias_addr):
                    msg = _('This payment request will be signed.') + '\n' + _('Please enter your password')
                    password = self.password_dialog(msg)
                    if password:
                        try:
                            self.wallet.sign_payment_request(addr, alias, alias_addr, password)
                        except Exception as e:
                            self.show_error(str(e))
                            return
                    else:
                        return
                else:
                    return

    def pay_to_URI(self, URI, errFunc : callable = None):
        utils.NSLog("PayTo URI: %s", str(URI))
        if not URI or not self.wallet:
            return
        try:
            out = web.parse_URI(URI, self.on_pr)
        except Exception as e:
            if not callable(errFunc):
                self.show_error(_('Invalid bitcoincash URI:') + '\n' + str(e))
            else:
                errFunc()
            return
        r = out.get('r')
        sig = out.get('sig')
        name = out.get('name')
        if r or (name and sig):
            #self.prepare_for_payment_request()
            print("TODO: prepare_for_payment_request")
            return
        self.show_send_modal()
        address = out.get('address')
        amount = out.get('amount')
        label = out.get('label')
        message = out.get('message')
        # use label as description (not BIP21 compliant)
        self.sendVC.onPayTo_message_amount_(address,message,amount)
    
    def refresh_all(self):
        self.refresh_components('*')
        
    def refresh_components(self, *args) -> None:
        # BEGIN SPECIAL LOGIC TO RATE-LIMIT refresh_components spam
        dummy = "dummy_for_queue"
        #utils.NSLog("refresh_components...")
        #print(*args)
        if not args: args = ['*']
        doLater = False
        abortEarly = False
        self.queued_refresh_components_mut.acquire() # Lock
        qsize = len(self.queued_refresh_components)
        #oldq = self.queued_refresh_components.copy()
        # pick up queued as well as this call's components for refreshing..
        components = set(map(lambda x: str(x).strip().lower(),args)) | self.queued_refresh_components 
        self.queued_refresh_components = set() # immediately empty queue while we hold the lock
        diff = time.time() - float(self.last_refresh)
        if {dummy} == components: # spurious self-call
            abortEarly = True
        else:
            if diff < 0.300: 
                # rate-limit to 300ms between refreshes
                doLater = True
                self.queued_refresh_components = components.copy()
            else:
                # ok, we're going to refresh this time around.. update timestamp
                self.last_refresh = time.time() 
        self.queued_refresh_components_mut.release() # Unlock

        if abortEarly:
            #print("refresh_components: aborting early.. got dummy set...")
            return
            
        if doLater:
            # enqueue a call to this function at most 1 times
            if not qsize:
                #print("refresh_components: rate limiting.. calling later ",diff,"(",*args,")")
                utils.call_later((0.300-diff) + 0.010, lambda: self.refresh_components(dummy))
            else:
                # already had a queue -- this means another call_later() is pending, so do nothing but return and assume subsequent
                # call_later() will execute this function in the future.
                pass
                #print("refresh_components: already Queued! Q=",oldq)
            return
        # END SPECIAL LOGIC TO RATE-LIMIT refresh_components spam
        
        signalled = set()         
        al = {'*','all','world','everything'}
        #print("components: ",*components)
        if components & {'helper', *al} and self.sigHelper not in signalled:
            signalled.add(self.sigHelper)
            self.sigHelper.emit()
        if components & {'history', *al} and self.sigHistory not in signalled:
            signalled.add(self.sigHistory)
            self.sigHistory.emit()  # implicitly does an emptyCache() then emit()
            if self.sigCoins not in signalled:
                signalled.add(self.sigCoins)
                self.sigCoins.emit()
        if components & {'address', 'addresses', *al} and self.sigAddresses not in signalled:
            signalled.add(self.sigAddresses)
            self.sigAddresses.emit()
            if self.sigCoins not in signalled:
                signalled.add(self.sigCoins)
                self.sigCoins.emit()
        if components & {'prefs', 'preferences', 'settings', *al} and self.sigPrefs not in signalled:
            signalled.add(self.sigPrefs)
            self.sigPrefs.emit()
        if components & {'receive', 'requests', 'paymentrequests', 'pr', *al} and self.sigRequests not in signalled:
            signalled.add(self.sigRequests) 
            self.sigRequests.emit() # implicitly does an emptyCache() then emit()
        if components & {'network', 'servers','connection', 'interfaces', *al} and self.sigNetwork not in signalled:
            signalled.add(self.sigNetwork)
            self.sigNetwork.emit()
        # history implies contacts refresh because contacts contain HistoryEntries embedded in them.. so need to rebuild
        if components & {'contact', 'contacts', 'history', *al} and self.sigContacts not in signalled:
            signalled.add(self.sigContacts)
            self.sigContacts.emit() # implicitly does an emptyCache() then emit()

    def empty_caches(self, doEmit = False):
        self.sigHistory.emptyCache(noEmit=not doEmit)
        self.sigRequests.emptyCache(noEmit=not doEmit)
        self.sigContacts.emptyCache(noEmit=not doEmit)
        

    def on_new_daemon(self):
        self.daemon.gui = self
        self.open_last_wallet()
        self.register_network_callbacks()
        self.refresh_all()
        
    def on_low_memory(self) -> None:
        utils.NSLog("GUI: Low memory")
        if self.downloadingNotif_view is not None and self.downloadingNotif is None:
            self.downloadingNotif_view.release()
            self.downloadingNotif_view = None
            utils.NSLog("Released cached 'downloading notification banner view' due to low memory")
        
    def stop_daemon(self):
        if not self.daemon_is_running(): return
        self.unregister_network_callbacks()
        self.empty_caches(doEmit=False)
        if self.wallet and self.wallet.storage:
            self.daemon.stop_wallet(self.wallet.storage.path)
        self.daemon.stop()
        self.wallet = None
        self.daemon = None
        
    def start_daemon(self):
        if self.daemon_is_running(): return
        import electroncash.daemon as ed
        fd, server = ed.get_fd_or_server(self.config)
        self.daemon = ed.Daemon(self.config, fd, True)
        self.daemon.start()
        self.on_new_daemon()

    def daemon_is_running(self) -> bool:
        return self.daemon is not None and self.daemon.is_running()

    def open_last_wallet(self):
        self.config.open_last_wallet()
        path = self.config.get_wallet_path()


        # hard code some stuff for testing
        self.daemon.network.auto_connect = True
        self.config.set_key('auto_connect', self.daemon.network.auto_connect, True)
        print("WALLET PATH: %s"%path)
        #print ("NETWORK: %s"%str(self.daemon.network))
        w = self.do_wallet_stuff(path, self.config.get('url'))
        assert w
        # TODO: put this stuff in the UI
        self.wallet = w
        self.ext_txn_check()
        
    @staticmethod
    def forever_prompt_for_password_on_wallet(path_or_storage, msg = None) -> str:
        storage = WalletStorage(path_or_storage, manual_upgrades=True) if not isinstance(path_or_storage, WalletStorage) else path_or_storage
        if not storage.file_exists():
            raise WalletFileNotFound('Wallet File Not Found')
        pw_ok = False
        password = None
        while not pw_ok and storage.is_encrypted():
            password = ElectrumGui.prompt_password(msg)
            if not password:
                ElectrumGui.gui.show_error(message=_("A password is required to open this wallet"), title=_('Password Required'), localRunLoop = True)
                continue
            try:
                storage.decrypt(password)
            except:
                ElectrumGui.gui.show_error(message=_("The password was incorrect for this encrypted wallet, please try again."),
                                           title=_('Password Incorrect'), localRunLoop = True)
                continue
            pw_ok = True
        return password

    @staticmethod
    def prompt_password(prmpt = None, dummy=0):
        if ElectrumGui.gui:
            pw = password_dialog.prompt_password_local_runloop(vc=ElectrumGui.gui.get_presented_viewcontroller(),
                                                                prompt=prmpt)
            return pw
    
    def password_dialog(self, msg = None) -> str:
        return ElectrumGui.prompt_password(msg)
    
    def prompt_password_if_needed_asynch(self, callBack, prompt = None, title = None, vc = None) -> ObjCInstance:
        if self.wallet is None: return None
        if not self.wallet.has_password():
            callBack(None)
            return
        def cb(pw : str) -> None:
            try:
                if not self.wallet:
                    return # cancel
                self.wallet.check_password(pw)
                callBack(pw)
            except Exception as e:
                self.show_error(str(e), onOk = lambda: self.prompt_password_if_needed_asynch(callBack, prompt, title))
        return password_dialog.prompt_password_asynch(vc if vc else self.get_presented_viewcontroller(), cb, prompt, title)

    def generate_wallet(self, path):
        with open(path, "wb") as fdesc:
            fdesc.write(hardcoded_testing_wallet)
            fdesc.close()
            print("Generated hard-coded wallet -- wrote %d bytes"%len(hardcoded_testing_wallet))
        storage = WalletStorage(path, manual_upgrades=True)
        if not storage.file_exists():
            return
        ElectrumGui.forever_prompt_for_password_on_wallet(storage, "Test wallet password is: bchbch")
        if storage.requires_split():
            return
        if storage.requires_upgrade():
            return
        if storage.get_action():
            return
        wallet = Wallet(storage)
        return wallet

    def do_wallet_stuff(self, path, uri):
        wallet = None
        password = None
        try:
            password = ElectrumGui.forever_prompt_for_password_on_wallet(path)            
            wallet = self.daemon.load_wallet(path, password)
        except WalletFileNotFound as e:
            pass # continue below to generate wallet
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return
        if not wallet:
            try:
                wallet = self.generate_wallet(path)
            except Exception as e:
                print_error('[do_wallet_stuff] Exception caught', e)
            if not wallet:
                print("NO WALLET!!!")
                sys.exit(1)
            wallet.start_threads(self.daemon.network)
            self.daemon.add_wallet(wallet)
        return wallet

    def sign_tx_with_password(self, tx, callback, password, vc = None):
        '''Sign the transaction in a separate thread.  When done, calls
        the callback with a success code of True or False.
        '''
        # call hook to see if plugin needs gui interaction
        run_hook('sign_tx', self, tx)
        if not vc:
            vc = self.get_presented_viewcontroller()

        def on_error(exc_info):
            if not isinstance(exc_info[1], UserCancelled):
                if not isinstance(exc_info[1], InvalidPassword):
                    traceback.print_exception(*exc_info)
                self.show_error(str(exc_info[1]))
        def on_signed(result):
            callback(True)
        def on_failed(exc_info):
            on_error(exc_info)
            callback(False)

        if False:#self.tx_external_keypairs:
            task = partial(Transaction.sign, tx, self.tx_external_keypairs)
        else:
            task = partial(self.wallet.sign_transaction, tx, password)
        utils.WaitingDialog(vc, _('Signing transaction...'), task,
                            on_signed, on_failed)

    def broadcast_transaction(self, tx, tx_desc, doneCallback = None, vc = None):
        if not vc:
            vc = self.get_presented_viewcontroller()
        def broadcast_thread(): # non-GUI thread
            #pr = self.payment_request
            #if pr and pr.has_expired():
            #    self.payment_request = None
            #    return False, _("Payment request has expired")
            status, msg =  self.daemon.network.broadcast(tx)
            #if pr and status is True:
            #    self.invoices.set_paid(pr, tx.txid())
            #    self.invoices.save()
            #    self.payment_request = None
            #    refund_address = self.wallet.get_receiving_addresses()[0]
            #    ack_status, ack_msg = pr.send_ack(str(tx), refund_address)
            #    if ack_status:
            #        msg = ack_msg
            return status, msg

        # Capture current TL window; override might be removed on return
        parent = self#.top_level_window()

        def broadcast_done(result):
            # GUI thread
            if result:
                status, msg = result
                if status:
                    if tx_desc is not None and tx.is_complete():
                        self.wallet.set_label(tx.txid(), tx_desc)
                    onOk = None
                    if callable(doneCallback):
                        onOk = doneCallback
                    def myCallback() -> None:
                        if onOk: onOk()
                        #self.invoice_list.update()
                        if self.sendVC and not self.sendVC.isBeingDismissed():
                            self.sendVC.clear()
                            self.sendVC.dismissOnAppear = True
                            if self.sendVC.presentingViewController and not self.sendVC.presentedViewController and self.sendNav and self.sendNav.topViewController.ptr.value == self.sendVC.ptr.value:
                                self.sendVC.presentingViewController.dismissViewControllerAnimated_completion_(True, None)
                    parent.show_message(message=_('Payment sent.') + '\n' + msg, onOk = myCallback)
                else:
                    parent.show_error(msg)
        def on_error(exc_info):
            if not isinstance(exc_info[1], UserCancelled):
                traceback.print_exception(*exc_info)
                self.show_error(str(exc_info[1]))

        utils.WaitingDialog(vc, _('Broadcasting transaction...'),
                            broadcast_thread, broadcast_done, on_error)

    def change_password(self, oldpw : str, newpw : str, enc : bool) -> None:
        print("change pw, old=",oldpw,"new=",newpw, "enc=", str(enc))
        try:
            self.wallet.update_password(oldpw, newpw, enc)
        except BaseException as e:
            self.show_error(str(e))
            return
        except:
            traceback.print_exc(file=sys.stdout)
            self.show_error(_('Failed to update password'))
            return
        msg = _('Password was updated successfully') if newpw else _('Password is disabled, this wallet is not protected')
        self.show_message(msg, title=_("Success"))
        self.refresh_components('helper')
        

    def show_change_password(self, msg = None, vc = None):
        if self.wallet is None or self.wallet.storage is None: return
        pwvc = password_dialog.Create_PWChangeVC(msg, self.wallet.has_password(), self.wallet.storage.is_encrypted(), self.change_password)
        (self.get_presented_viewcontroller() if not vc else vc).presentViewController_animated_completion_(pwvc, True, None)


    def protected(func):
        '''Password request wrapper.  The password is passed to the function
        as the 'password' named argument.  "None" indicates either an
        unencrypted wallet, or the user cancelled the password request.
        An empty input is passed as the empty string.'''
        def request_password(self, *args, **kwargs):
            if self.wallet is None: return
            password = None
            while self.wallet.has_password():
                password = self.password_dialog()
                if password is None:
                    # User cancelled password input
                    return
                try:
                    self.wallet.check_password(password)
                    break
                except Exception as e:
                    self.show_error(str(e), localRunLoop = True)
                    continue

            kwargs['password'] = password
            return func(self, *args, **kwargs)
        return request_password

    @protected
    def show_seed_dialog(self, password):
        self.show_seed_dialog2(password)
        
    def show_seed_dialog2(self, password, vc = None):
        if self.wallet is None or self.wallet.storage is None: return
        if not self.wallet.has_seed():
            self.show_message(_('This wallet has no seed'))
            return
        keystore = self.wallet.get_keystore()
        seed = ""
        passphrase = ""
        try:
            seed = keystore.get_seed(password)
            passphrase = keystore.get_passphrase(password)
        except BaseException as e:
            self.show_error(str(e))
            return
        seedvc = seed_dialog.Create_SeedDisplayVC(seed, passphrase)
        (vc if vc else self.get_presented_viewcontroller()).presentViewController_animated_completion_(seedvc, True, None)

    def show_network_dialog(self, vc = None) -> None:
        ''' Provide this dialog on-demand to save on startup time and/or on memory consumption '''
        if self.networkNav is not None:
            utils.NSLog("**** WARNING **** Network Nav is not None!! FIXME!")
        if not self.daemon:
            utils.NSLog('"Show Network Dialog" request failed -- daemon is not active!')
            return
        self.networkVC = network_dialog.NetworkDialogVC.new().autorelease()
        self.networkVC.title = _("Network")
        self.networkNav = utils.tintify(UINavigationController.alloc().initWithRootViewController_(self.networkVC).autorelease())
        def doCleanup(oid : objc_id) -> None:
            if self.networkVC is not None and oid == self.networkVC.ptr:
                #print("NetworkDialogVC dealloc caught!")
                self.networkVC = None
            if self.networkNav is not None and oid == self.networkNav.ptr:
                #print("Network Nav dealloc caught!")
                self.networkNav = None
        utils.NSDeallocObserver(self.networkVC).connect(doCleanup)
        utils.NSDeallocObserver(self.networkNav).connect(doCleanup)
        self.add_navigation_bar_close_to_modal_vc(self.networkVC)
        (vc if vc else self.get_presented_viewcontroller()).presentViewController_animated_completion_(self.networkNav, True, None)
    
    def send_create_if_none(self) -> None:
        if self.sendVC: return
        self.sendVC = send.SendVC.alloc().init().autorelease()
        self.sendNav = utils.tintify(UINavigationController.alloc().initWithRootViewController_(self.sendVC).autorelease())
        self.add_navigation_bar_close_to_modal_vc(self.sendVC, leftSide = True)
        def doCleanup(oid : objc_id) -> None:
            self.sendVC = None
            self.sendNav = None
        utils.NSDeallocObserver(self.sendVC).connect(doCleanup)
     
    def show_send_modal(self, vc = None) -> None:
        self.send_create_if_none()
        if not self.tabController or not self.sendNav: return
        if self.sendNav.topViewController.ptr.value != self.sendVC.ptr.value:
            self.sendNav.popToRootViewControllerAnimated_(False)
        if self.sendNav.presentingViewController: return # already presented, return early
        if not vc: vc = self.get_presented_viewcontroller()
        vc.presentViewController_animated_completion_(self.sendNav, True, None)
     
    def show_receive_modal(self, vc = None) -> None:
        self.receive_create_if_none()
        if not self.tabController or not self.receiveNav: return
        if self.receiveNav.topViewController.ptr.value != self.receiveVC.ptr.value:
            self.receiveNav.popToRootViewControllerAnimated_(False)
        if self.receiveNav.presentingViewController: return # already presented, return early
        if not vc: vc = self.get_presented_viewcontroller()
        vc.presentViewController_animated_completion_(self.receiveNav, True, None)
        
    def show_addresses_tab(self) -> None:
        if not self.tabController or not self.addressesNav: return
        self.tabController.selectedViewController = self.addressesNav
        if self.addressesNav.topViewController.ptr.value != self.addressesVC.ptr.value:
            self.addressesNav.popToRootViewControllerAnimated_(True)
        
    def jump_to_send_with_spend_from(self, coins, vc = None) -> None:
        self.send_create_if_none()
        utils.nspy_put_byname(self.sendVC, coins, 'spend_from')
        self.show_send_modal(vc=vc)

    def jump_to_send_with_pay_to(self, addr, vc = None) -> None:
        self.send_create_if_none()
        utils.nspy_put_byname(self.sendVC, addr, 'pay_to')
        self.show_send_modal(vc=vc)

    def receive_create_if_none(self) -> None:
        if self.receiveVC: return
        # Receive modal
        self.receiveVC = receive.ReceiveVC.alloc().init().autorelease()
        self.receiveNav = utils.tintify(UINavigationController.alloc().initWithRootViewController_(self.receiveVC).autorelease())
        self.add_navigation_bar_close_to_modal_vc(self.receiveVC, leftSide = True)
        def doCleanup(oid : objc_id) -> None:
            self.receiveVC = None
            self.receiveNav = None
        utils.NSDeallocObserver(self.receiveVC).connect(doCleanup)
        
    def jump_to_receive_with_address(self, address) -> None:
        self.receive_create_if_none()
        if not isinstance(address, (Address, str)): return
        self.receiveVC.addr = (str(address))
        self.show_receive_modal()
        
    def jump_to_addresses_with_address(self, address) -> None:
        if not isinstance(address, Address) or not self.addressesNav or not self.wallet or not self.wallet.is_mine(address): return
        self.show_addresses_tab()
        self.addressesVC.focusAddress_(address.to_ui_string())

    def save_tabs_order(self, vcs : list = None) -> None:
        if not self.tabController or not self.config: return
        vcs = py_from_ns(self.tabController.viewControllers) if not vcs else vcs
        order = list()
        for vc in vcs:
            for i,tab in enumerate(self.tabs):
                if vc.ptr.value == tab.ptr.value:
                    order.append(str(i))
                    #print("%s = %d"%(vc.title,i))
        self.config.set_key('tab_order', ','.join(order), True)
            
    def get_history_entry(self, tx_hash) -> tuple:
        ''' returns a history.HistoryEntry namedtuple instance if tx_hash exists in history, or None if not found '''
        history = self.sigHistory.get(None)
        if history:
            for entry in history:
                if entry.tx_hash == tx_hash:
                    return entry
        return None
    
    def get_address_entry(self, address) -> tuple:
        ''' returns an addresses.AddrData.Entry namedtuple or None if not found. Accepts either a string or an Address instance'''
        if isinstance(address, str):
            address = Address.from_string(address)
        addrData = utils.nspy_get_byname(self.addressesVC, 'addrData')
        sdict = addrData.getSections() if addrData else dict()
        for k in sdict.keys():
            section = sdict[k]
            for entry in section[1]: # first 'entry' in array is a section name, second element is the list of addresses
                if address == entry.address:
                    return entry
        return None
            
    def open_ext_txn(self, data : str) -> None:
        if not self.wallet:
            self.queued_ext_txn = data
        else:
            self.show_ext_txn(data)
 
    def ext_txn_check(self) -> None:
        if self.queued_ext_txn and self.wallet and self.window and self.tabController and self.window.rootViewController and self.window.rootViewController.ptr.value == self.tabController.ptr.value:
            txn = self.queued_ext_txn
            self.queued_ext_txn = None
            self.show_ext_txn(txn)
           
    def show_ext_txn(self, txn : str) -> None:
        if isinstance(txn, bytes):
            txn = txn.decode('utf-8')
            print("Warning: show_ext_txn got bytes instead of a str for the txn.. this may be bad...")
        from electroncash.transaction import tx_from_str, Transaction
        from . import txdetail
        try:
            txt_tx = tx_from_str(txn)
            tx = Transaction(txt_tx)
            tx.deserialize()
            if self.wallet:
                my_coins = self.wallet.get_spendable_coins(None, self.config)
                my_outpoints = [vin['prevout_hash'] + ':' + str(vin['prevout_n']) for vin in my_coins]
                for i, txin in enumerate(tx.inputs()):
                    outpoint = txin['prevout_hash'] + ':' + str(txin['prevout_n'])
                    if outpoint in my_outpoints:
                        my_index = my_outpoints.index(outpoint)
                        tx._inputs[i]['value'] = my_coins[my_index]['value']
            print("ext txn read ok")
            if self.has_modal():
                self.show_error(_("Cannot display the requested transaction since you already have a modal dialog open."))
            else:
                vc = self.get_presented_viewcontroller()
                txvc = txdetail.CreateTxDetailWithTx(tx, asModalNav = True)
                vc.presentViewController_animated_completion_(txvc, True, None)
        except:
            traceback.print_exc(file=sys.stderr)
            self.show_error(_("Electron Cash was unable to parse your transaction"))
            return


    # this method is called by Electron Cash libs to start the GUI
    def main(self):
        import hashlib
        print("HashLib algorithms available: " + str(hashlib.algorithms_available))
        import platform
        print ("Platform %s uname: %s"%(platform.platform(),platform.uname()))
        print ("Bundle Identifier %s"% utils.bundle_identifier)

        try:
            self.init_network()
        except:
            traceback.print_exc(file=sys.stdout)
            return
        
        self.open_last_wallet()
        
        self.createAndShowUI()
        self.ext_txn_check()
