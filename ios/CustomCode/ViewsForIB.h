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
@end

#endif /* ViewsForIB_h */
