//
//  ViewsForIB.h
//  Electron-Cash
//
//  Created by calin on 4/7/18.
//  Copyright © 2018 Calin Culianu. All rights reserved.
//

#ifndef ViewsForIB_h
#define ViewsForIB_h

#import <UIKit/UIKit.h>
#import "DZNSegmentedControl/DZNSegmentedControl.h"
#import "UIKitExtras.h"
#import "CCActivityIndicator/CCActivityIndicator.h"
#import "KeyboardVC/KeyboardVC.h"


@interface AddrConvBase : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *blurb;
@property (nonatomic, weak) IBOutlet UILabel *cashTit;
@property (nonatomic, weak) IBOutlet UILabel *cash;
@property (nonatomic, weak) IBOutlet UILabel *legacyTit;
@property (nonatomic, weak) IBOutlet UILabel *legacy;
@property (nonatomic, weak) IBOutlet UITextField *address;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyCashBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyLegBut;
- (IBAction) onBut:(id)sender;
- (IBAction) onAddress:(id)sender;
@end

@interface NewContactBase : UIViewController
@property (nonatomic, weak) IBOutlet UIBarButtonItem *okBut;
@property (nonatomic, weak) IBOutlet UILabel *nameTit;
@property (nonatomic, weak) IBOutlet UITextField *name;
@property (nonatomic, weak) IBOutlet UILabel *addressTit;
@property (nonatomic, weak) IBOutlet UITextField *address;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyAddressBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyNameBut;
@end

// stub for Python -- implemented in contacts.py
@interface NewContactVC : NewContactBase
-(IBAction) onQR;
-(IBAction) onOk;
-(IBAction) onCancel;
-(IBAction) onCpy:(id)sender;
@end

// dummy stub for Interface Builder -- actual implementation is in python in amountedit.py
@interface BTCAmountEdit : UITextField
@end
// dummy stub for Interface Builder -- actual implementation is in python in amountedit.py
@interface FiatAmountEdit : BTCAmountEdit
@end
// dummy stub for Interface Builder -- actual implementation is in python in feeslider.py
@interface FeeSlider : UISlider
@end

@interface SendBase : UIViewController
@property (nonatomic, weak) IBOutlet UIView *contentView;
@property (nonatomic, weak) IBOutlet UILabel *payToTit;
@property (nonatomic, weak) IBOutlet UITextField *payTo;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
@property (nonatomic, weak) IBOutlet UIButton *contactBut;
@property (nonatomic, weak) IBOutlet UILabel *descTit;
@property (nonatomic, weak) IBOutlet UITextField *desc;
@property (nonatomic, weak) IBOutlet UILabel *amtTit;
@property (nonatomic, weak) IBOutlet BTCAmountEdit *amt;
@property (nonatomic, weak) IBOutlet UIButton *maxBut;
@property (nonatomic, weak) IBOutlet UILabel *fiatTit;
@property (nonatomic, weak) IBOutlet FiatAmountEdit *fiat;
@property (nonatomic, weak) IBOutlet UILabel *feeTit;
@property (nonatomic, weak) IBOutlet UISlider *feeSlider;
@property (nonatomic, weak) IBOutlet UILabel *feeLbl;
@property (nonatomic, weak) IBOutlet BTCAmountEdit *feeTf;
@property (nonatomic, weak) IBOutlet UILabel *feeTfLbl;
@property (nonatomic, weak) IBOutlet UIBarButtonItem *clearBut;
@property (nonatomic, weak) IBOutlet UIBarButtonItem *previewBut;
@property (nonatomic, weak) IBOutlet UIButton *sendBut; // actually a subview of a UIBarButtonItem
@property (nonatomic, weak) IBOutlet UILabel *message;
@property (nonatomic, weak) IBOutlet UILabel *spendFromTit;
@property (nonatomic, weak) IBOutlet UIButton *clearSFBut;
@property (nonatomic, weak) IBOutlet UITextView *spendFrom;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *csFeeTop;

-(IBAction)onQRBut:(id)sender; // implemented in python send.py
-(IBAction)onContactBut:(id)sender; // implemented in python send.py
-(IBAction)clear; // implemented in python send.py
-(IBAction)onPreviewSendBut:(id)sender; // implemented in python send.py
-(IBAction)clearSpendFrom; // implemented in python send.py
-(IBAction)spendMax; // implemented in python send.py
@end


@interface TxDetailBase : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *txTit;
@property (nonatomic, weak) IBOutlet UILabel *txHash;
@property (nonatomic, weak) IBOutlet UIButton *cpyBut;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
//# Description:
@property (nonatomic, weak) IBOutlet UILabel *descTit;
@property (nonatomic, weak) IBOutlet UITextField *descTf;
//# Status:
@property (nonatomic, weak) IBOutlet UILabel *statusTit;
@property (nonatomic, weak) IBOutlet UIImageView *statusIV;
@property (nonatomic, weak) IBOutlet UILabel *statusLbl;
//# Date:
@property (nonatomic, weak) IBOutlet UILabel *dateTit;
@property (nonatomic, weak) IBOutlet UILabel *dateLbl;
//# Amount received/sent:
@property (nonatomic, weak) IBOutlet UILabel *amtTit;
@property (nonatomic, weak) IBOutlet UILabel *amtLbl;
//# Size:
@property (nonatomic, weak) IBOutlet UILabel *sizeTit;
@property (nonatomic, weak) IBOutlet UILabel *sizeLbl;
//# Fee:
@property (nonatomic, weak) IBOutlet UILabel *feeTit;
@property (nonatomic, weak) IBOutlet UILabel *feeLbl;
//# Locktime:
@property (nonatomic, weak) IBOutlet UILabel *lockTit;
@property (nonatomic, weak) IBOutlet UILabel *lockLbl;
//# Inputs
@property (nonatomic, weak) IBOutlet UITableView *inputsTV;
//# Outputs
@property (nonatomic, weak) IBOutlet UITableView *outputsTV;

- (IBAction) onCpyBut:(id)sender; // overridden in TxDetail (python)
- (IBAction) onQRBut:(id)sender; // overridden in TxDetail (python)
@end

@interface TxInputsOutputsTVCBase : NSObject
@property (nonatomic, weak) TxDetailBase *txDetailVC; // the TxDetail that is holding us
@end

@interface WalletsNavBase : UINavigationController
@end

typedef NS_ENUM(NSInteger, WalletsStatusMode) {
    WalletsStatusOffline = 0,
    WalletsStatusOnline = 1,
    WalletsStatusDownloadingHeaders = 2,
    WalletsStatusSynchronizing = 3
};

@class WalletsDrawerVC;
@class TxHistoryHelper;
@class ReqTVD;

@interface WalletsVCBase : UIViewController
@property (nonatomic,assign) WalletsStatusMode status;
@property (nonatomic,weak) IBOutlet UILabel *statusLabel;
@property (nonatomic,weak) IBOutlet UILabel *statusBlurb;

#pragma mark Top Nav Bar related
@property (nonatomic, weak) IBOutlet UINavigationBar *navBar;
@property (nonatomic, weak) IBOutlet UIView *blueBarTop;

#pragma mark Drawer Related
@property (nonatomic, weak) IBOutlet WalletsDrawerVC *modalDrawerVC;
@property (nonatomic, weak) IBOutlet UILabel *walletName, *walletAmount, *walletUnits;

#pragma mark Main View Area Related
@property (nonatomic, weak) IBOutlet DZNSegmentedControl *segControl;
@property (nonatomic, strong) IBOutlet TxHistoryHelper *txsHelper; ///< txsHelper.tv is the tableView
@property (nonatomic, strong) IBOutlet ReqTVD *reqTVD; ///< reqstv is the tableView
@property (nonatomic, weak) IBOutlet UITableView *reqstv;
@property (nonatomic, weak) IBOutlet UIView *noTXsView; ///< displays a message and shows an image when the txsHelper.tv table is empty
@property (nonatomic, weak) IBOutlet UIView *noReqsView; ///< displays a message and shows an image when the reqstv table is empty
@property (nonatomic, weak) IBOutlet UIButton *sendBut;
@property (nonatomic, weak) IBOutlet UIButton *receiveBut;
@end

// stub to represent python -- implemented in python wallets.py
@interface WalletsVC : WalletsVCBase
-(IBAction)toggleDrawer; // declared here for IB, implemented in python wallets.py
-(IBAction)didChangeSegment:(DZNSegmentedControl *)control; // implemented in python wallets.py
-(IBAction)onSendBut;
-(IBAction)onReceiveBut;
-(IBAction)onTopNavTap;
@end
// stub to represent python -- implemented in python wallets.py
@interface WalletsNav : WalletsNavBase
@end
@interface WalletsDrawerVCBase : UIViewController
@property (nonatomic, weak) IBOutlet WalletsVC *vc; // parent viewcontroller that presented us
@property (nonatomic, weak) IBOutlet UIImageView *chevron;
@property (nonatomic, weak) IBOutlet UILabel *name, *amount, *units; // top labels
@property (nonatomic, weak) IBOutlet UIView *drawer; // the wallet 'drawer' dropdown
@property (nonatomic, weak) IBOutlet UIView *drawerBottom; // the wallet 'drawer' dropdown's bottom (sometimes hidden) area
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *drawerHeight;
@property (nonatomic, weak) IBOutlet UITableView *tv;
@property (nonatomic, strong) IBOutlet UIView *tableHeader, *tableFooter;
@property (nonatomic, assign) BOOL isOpen;
-(void)openAnimated:(BOOL)animated;
-(void)closeAnimated:(BOOL)animated;
@end
// stub to represent python -- implemented in python wallets.py
@interface WalletsDrawerVC : WalletsDrawerVCBase
-(IBAction)addWallet;
@end

@interface TxHistoryHelperBase : NSObject
@property (nonatomic, weak) IBOutlet UIViewController *vc;
@property (nonatomic, weak) IBOutlet UITableView *tv;
@property (nonatomic, assign) BOOL compactMode;
@end
// stub to represent python -- implemented in python wallets.py
@interface TxHistoryHelper : TxHistoryHelperBase
@end

@interface TxHistoryCell : UITableViewCell
@property (nonatomic, weak) IBOutlet UIImageView *icon;
@property (nonatomic, weak) IBOutlet UILabel *amountTit;
@property (nonatomic, weak) IBOutlet UILabel *amount;
@property (nonatomic, weak) IBOutlet UILabel *balanceTit;
@property (nonatomic, weak) IBOutlet UILabel *balance;
@property (nonatomic, weak) IBOutlet UILabel *date;
@property (nonatomic, weak) IBOutlet UILabel *desc;
@property (nonatomic, weak) IBOutlet UILabel *statusTit;
@property (nonatomic, weak) IBOutlet UIImageView *statusIcon;
@property (nonatomic, weak) IBOutlet UILabel *status;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *amtTitCS;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *amtCS;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *dateCS;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *descCS;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *dateWidthCS;
@end

@interface ReqTVDBase : NSObject
@property (nonatomic, weak) IBOutlet UITableView *tv;
@end

// stub to represent python -- implemented in python receive.py
@interface ReqTVD : ReqTVDBase
@end


@interface RequestListCell : UITableViewCell
@property (nonatomic, weak) IBOutlet UILabel *addressTit;
@property (nonatomic, weak) IBOutlet UILabel *address;
@property (nonatomic, weak) IBOutlet UILabel *amountTit;
@property (nonatomic, weak) IBOutlet UILabel *amount;
@property (nonatomic, weak) IBOutlet UILabel *statusTit;
@property (nonatomic, weak) IBOutlet UILabel *status;
@property (nonatomic, weak) IBOutlet UILabel *date;
@property (nonatomic, weak) IBOutlet UILabel *desc;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *addressTitCS;
@end

@interface ContactsVCBase : UIViewController
@property (nonatomic, weak) IBOutlet UIView *noContacts;
@property (nonatomic, weak) IBOutlet UILabel *noContactsLabel;
@property (nonatomic, weak) IBOutlet UIButton *butBottom;
@property (nonatomic, weak) IBOutlet UIRefreshControl *refreshControl; // bound in python
@property (nonatomic, weak) IBOutlet UITableView *tv;
@end

// stub to represent python -- implemented in python contacts.py
@interface ContactsVC : ContactsVCBase
-(IBAction) onAddBut;
@end

@interface ContactsCell : UITableViewCell
@property (nonatomic, weak) IBOutlet UIImageView *customAccessory;
@property (nonatomic, weak) IBOutlet UILabel *name;
@property (nonatomic, weak) IBOutlet LinkLabel *address;
@property (nonatomic, weak) IBOutlet UILabel *numTxs;
@end

@interface ContactDetailVCBase: UIViewController
@property (nonatomic, weak) IBOutlet UILabel *name;
@property (nonatomic, weak) IBOutlet UIImageView *qr;
@property (nonatomic, weak) IBOutlet UILabel *address;
@property (nonatomic, weak) IBOutlet UITableView *tv;
@property (nonatomic, weak) IBOutlet UIButton *payToBut;
@property (nonatomic, weak) TxHistoryHelper *helper;
@end

// stub for python -- implemented in contacts.py
@interface ContactDetailVC : ContactDetailVCBase
- (IBAction) onPayTo;
- (IBAction) cpyAddressToClipboard;
- (IBAction) cpyNameToClipboard;
@end

@interface AddressesVCBase : UIViewController
@property (nonatomic, weak) IBOutlet UIView *topComboProxyL, *topComboProxyR;
@property (nonatomic, weak) IBOutlet UILabel *topLblL, *topLblR;
@property (nonatomic, weak) IBOutlet UITableView *tableView;
@end

// stub for python -- implemented in addresses.py
@interface AddressesVC : AddressesVCBase
- (IBAction) onTapComboProxyL;
- (IBAction) onTapComboProxyR;
- (IBAction) onTapAddress:(UIGestureRecognizer *)gr;
@end

@interface AddressesCell : UITableViewCell
@property (nonatomic, weak) IBOutlet LinkLabel *address;
@property (nonatomic, weak) IBOutlet UILabel *index, *balanceTit, *balance, *flags, *desc;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *topCS, *midCS;
@end

@class ECTextViewDelegate;

@interface AddressDetailBase : UIViewController
@property (nonatomic, strong) IBOutlet ECTextViewDelegate *descDel;
@property (nonatomic, weak) UIBarButtonItem *optionsBarBut;
@property (nonatomic, weak) IBOutlet UIImageView *qr;
@property (nonatomic, weak) IBOutlet UILabel *address, *balanceTit, *balance, *fiatBalance, *statusTit, *status, *descTit, *numTxTit, *numTx;
@property (nonatomic, weak) IBOutlet UITextView *desc;
@property (nonatomic, weak) IBOutlet UITableView *tv;
@property (nonatomic, weak) IBOutlet UIButton *freezeBut, *spendFromBut; // set .selected=YES/NO for checked/unchecked
@property (nonatomic, weak) IBOutlet UIGestureRecognizer *utxoGr; // enabled when they have nonzero utxos
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *txHistoryTopCS, *statusTopCS;
@property (nonatomic) CGFloat txHistoryTopSaved, statusTopSaved;
@end

// stub for python -- implemented in addresses.py
@interface AddressDetail : AddressDetailBase
- (IBAction) toggleFreezeAddress;
- (IBAction) cpyAddress;
- (void) onOptions;
- (IBAction) onSpendFrom;
- (IBAction) onUTXOs;
@end

@interface CoinsCell : UITableViewCell
@property (nonatomic, weak) IBOutlet LinkLabel *address;
@property (nonatomic, weak) IBOutlet UILabel *utxo, *amount, *height, *desc, *flags;
@property (nonatomic, weak) IBOutlet UILabel *amountTit, *utxoTit, *heightTit;
@property (nonatomic, weak) IBOutlet UIView *accessoryFlashView;
@property (nonatomic) BOOL chevronHidden; // defaults to NO. If YES cell will re-layout itself
@property (nonatomic) BOOL buttonSelected; // defaults to NO. If YES, button will have a checkmark and will be in the 'selected' state
@property (nonatomic) BOOL buttonEnabled; // defaults to YES. If YES, button will send events and select itself on tap. If NO, it will be grayed out
@property (nonatomic, copy) void(^onButton)(CoinsCell *cell); // set this block to define a callback for when the button is tapped due to user interaction. Not called if buttonSelected = YES is set programmatically!
@property (nonatomic, copy) void(^onAccessory)(CoinsCell *cell); // set this block to define a callback for when the accessory (chevron on right) is tapped.  If chevronHidden = true, no events will come.
@end


@interface CoinsDetailBase : UIViewController
@property (nonatomic, strong) IBOutlet ECTextViewDelegate *descDel;
@property (nonatomic, weak) UIBarButtonItem *optionsBarBut;
@property (nonatomic, weak) IBOutlet UIImageView *qr;
@property (nonatomic, weak) IBOutlet UILabel *address, *addressTit, *amountTit, *amount, *fiatAmount, *utxoTit, *utxo, *descTit, *heightTit, *height, *status;
@property (nonatomic, weak) IBOutlet UITextView *desc;
@property (nonatomic, weak) IBOutlet UIButton *freezeBut; // set .selected=YES/NO for checked/unchecked
@property (nonatomic, weak) IBOutlet UIButton *spendFromBut;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *addressTopCS, *statusTopCS;
@property (nonatomic) CGFloat addressTopSaved, statusTopSaved;
@end

// stub for python -- implemented in coins.py
@interface CoinsDetail : CoinsDetailBase
- (IBAction) toggleFreezeAddress;
- (IBAction) cpyAddress;
- (IBAction) cpyUTXO;
- (void) onOptions;
- (IBAction) onSpendFrom;
@end

@interface PleaseWaitVC : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *message, *pleaseWait;
@property (nonatomic, weak) IBOutlet CCActivityIndicator *activityIndicator;
@end

@interface NewWalletNav : UINavigationController
@property (nonatomic, strong) NSDictionary *params; // set by the viewcontrollers in a particular story sequence to set up wallet creation params
@end
@interface NewWalletVCBase : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *walletNameTit, *walletPw1Tit, *walletPw2Tit, *errMsg;
@property (nonatomic, weak) IBOutlet UITextField *walletName, *walletPw1, *walletPw2;
@property (nonatomic, weak) IBOutlet UIView *errMsgView;
@property (nonatomic, weak) IBOutlet UIButton *nextBut;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *nextButBotCS, *errHeightCS, *errTopCS;
@end
@interface NewWalletVC : NewWalletVCBase
// implemented in python newwallet.py..
@end

@interface NewWalletSeedBase : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *seedTit, *info;
@property (nonatomic, weak) IBOutlet UITextView *seedtv;
@property (nonatomic, weak) IBOutlet UIView *infoView;
@property (nonatomic, weak) IBOutlet UIButton *nextBut;

// below only used in NewWalletSeed2 child class
@property (nonatomic, weak) IBOutlet KeyboardVC *kvc;
@property (nonatomic, weak) IBOutlet UIView *kvcContainerView;
@property (nonatomic, weak) IBOutlet UIView *errMsgView;
@property (nonatomic, weak) IBOutlet UILabel *errMsg;
@end
@interface NewWalletSeed1 : NewWalletSeedBase
// implemented in python newwallet.py
@end
@interface NewWalletSeed2 : NewWalletSeedBase
// implemented in python newwallet.py
- (IBAction) onNext;
@end
@interface SuggestionButton : UIButton
+ (instancetype) suggestionButtonWithText:(NSString *)text handler:(void(^)(UIControl *))handler;
@end

@interface NewWalletMenuBase : UIViewController
@property (nonatomic, weak) IBOutlet UILabel *tit, *blurb;
@property (nonatomic, weak) IBOutlet UIButton *std, *restore, *imp, *master;
- (IBAction) dismiss;
// default impl does nothing -- implemented in python newwallet.py
- (IBAction) unimplemented;
@end
@interface NewWalletMenu : NewWalletMenuBase
// implemented in python newwallet.py
@end

@interface OnBoardingWizardBase : UIViewController
@end

@interface OnBoardingWizard : OnBoardingWizardBase
// implemented in python in newwallet.py
@end
@interface OnBoardingMenu : NewWalletMenuBase
// implemented in python newwallet.py
- (IBAction) onNewStandardWallet;
@end
#endif /* ViewsForIB_h */
