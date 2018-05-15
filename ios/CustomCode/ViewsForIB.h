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

@interface HistoryCellLarge : UITableViewCell
@property (nonatomic, weak) IBOutlet UIImageView *icon;
@property (nonatomic, weak) IBOutlet UILabel *status1;
@property (nonatomic, weak) IBOutlet UILabel *status2;
@property (nonatomic, weak) IBOutlet UILabel *amtTit;
@property (nonatomic, weak) IBOutlet UILabel *amt;
@property (nonatomic, weak) IBOutlet UILabel *balTit;
@property (nonatomic, weak) IBOutlet UILabel *bal;
@property (nonatomic, weak) IBOutlet UITextField *descTf;
@end


@interface CoinsCellLarge : UITableViewCell
@property (nonatomic, weak) IBOutlet UILabel *addressTit;
@property (nonatomic, weak) IBOutlet UILabel *address;
@property (nonatomic, weak) IBOutlet UILabel *flags;
@property (nonatomic, weak) IBOutlet UILabel *heightTit;
@property (nonatomic, weak) IBOutlet UILabel *height;
@property (nonatomic, weak) IBOutlet UILabel *amtTit;
@property (nonatomic, weak) IBOutlet UILabel *amt;
@property (nonatomic, weak) IBOutlet UILabel *utxoTit;
@property (nonatomic, weak) IBOutlet UILabel *utxo;
@property (nonatomic, weak) IBOutlet UITextField *descTf;
@property (nonatomic, weak) IBOutlet UIButton *cpyBut;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
@property (nonatomic, weak) IBOutlet UIButton *optionsBut;
@property (nonatomic, weak) IBOutlet UITapGestureRecognizer *addressGr;
@end

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
@property (nonatomic, weak) IBOutlet UILabel *blurb;
@property (nonatomic, weak) IBOutlet UILabel *nameTit;
@property (nonatomic, weak) IBOutlet UITextField *name;
@property (nonatomic, weak) IBOutlet UILabel *addressTit;
@property (nonatomic, weak) IBOutlet UITextField *address;
@property (nonatomic, weak) IBOutlet UIButton *qrBut;
@property (nonatomic, weak) IBOutlet UIButton *okBut;
@property (nonatomic, weak) IBOutlet UIButton *cancelBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyAddressBut;
@property (nonatomic, weak) IBOutlet UIButton *cpyNameBut;
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *topCS;
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

@class WalletsDrawerHelper;
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
@property (nonatomic, weak) IBOutlet UILabel *walletName;
@property (nonatomic, weak) IBOutlet UILabel *walletAmount;
@property (nonatomic, weak) IBOutlet UILabel *walletUnit;
@property (nonatomic, strong) IBOutlet WalletsDrawerHelper *drawerHelper;
@property (nonatomic, weak) UIView *addWalletView;

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
@interface WalletsDrawerHelperBase : NSObject
@property (nonatomic, weak) IBOutlet WalletsVC *vc;
@property (nonatomic, weak) IBOutlet UIImageView *chevron;
@property (nonatomic, weak) IBOutlet UIView *drawer; // the wallet 'drawer' dropdown
@property (nonatomic, weak) IBOutlet UIView *drawerBottom; // the wallet 'drawer' dropdown's bottom (sometimes hidden) area
@property (nonatomic, weak) IBOutlet NSLayoutConstraint *drawerHeight;
@property (nonatomic, weak) IBOutlet UITableView *tv;
@property (nonatomic, assign) BOOL isOpen;
-(void)openAnimated:(BOOL)animated;
-(void)closeAnimated:(BOOL)animated;
@end
// stub to represent python -- implemented in python wallets.py
@interface WalletsDrawerHelper : WalletsDrawerHelperBase
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

#endif /* ViewsForIB_h */
