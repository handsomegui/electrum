//
//  ViewsForIB.m
//  Electron-Cash
//
//  Created by calin on 4/7/18.
//  Copyright © 2018 Calin Culianu. All rights reserved.
//

#import "ViewsForIB.h"

#define DEGREES_TO_RADIANS(x) (M_PI * (x) / 180.0)

@implementation HistoryCellLarge
// properties get autosynthesized since Xcode 4.4
@end

@implementation CoinsCellLarge
// properties get autosynthesized since Xcode 4.4
@end

@implementation AddrConvBase
// properties get autosynthesized since Xcode 4.4
- (IBAction) onBut:(id)sender { /* implement in subclass.. */ }
- (IBAction) onAddress:(id)sender { /* implement in subclass.. */ }
@end

@implementation NewContactBase
// properties will be auto-synthesized
-(BOOL) textFieldShouldReturn:(UITextField *)tf {
    [tf resignFirstResponder];
    return YES;
}
@end

@implementation SendBase
// properties auto-synthesized
-(IBAction)onQRBut:(id)sender {} // implemented in python send.py
-(IBAction)onContactBut:(id)sender {} // implemented in python send.py
-(IBAction)clear {} // implemented in python send.py
-(IBAction)onPreviewSendBut:(id)sender {} // implemented in python send.py
-(IBAction)clearSpendFrom {} // implemented in python send.py
-(IBAction)spendMax {} // implemented in python send.py
@end

@implementation TxDetailBase
// properties auto-synthesized
- (IBAction) onCpyBut:(id)sender {} // overridden in TxDetail (python)
- (IBAction) onQRBut:(id)sender {} // overridden in TxDetail (python)
@end

@implementation TxInputsOutputsTVCBase
@end

@implementation WalletsNavBase
// properties auto-synthesized
@end

@implementation WalletsVCBase
// properties auto-synthesized
@end


@implementation WalletsDrawerHelperBase {
    BOOL isRotating;
}
// synthesized properties
-(void)closeAnimated:(BOOL)animated {

    CGRect frame = self.drawer.frame, frameBottom = self.drawerBottom.frame;
    frame.size.height = 63.0;
    frameBottom.size.height = 0.0;

    if (animated && !isRotating) {

        isRotating = YES;

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            self.chevron.transform = CGAffineTransformIdentity;
            self.drawer.frame = frame;
            self.drawerHeight.constant = 63.0;
            self.drawerBottom.frame = frameBottom;
            self.drawerBottom.hidden = YES;
        } completion:^(BOOL finished) {
            isRotating = NO;
            self.isOpen = NO;
        }];

    } else {
        [self.chevron.layer removeAllAnimations];
        self.chevron.transform = CGAffineTransformIdentity;
        self.drawer.frame = frame;
        self.drawerHeight.constant = 63.0;
        isRotating = NO;
        self.isOpen = NO;
        self.drawerBottom.hidden = YES;
        self.drawerBottom.frame = frameBottom;
    }
}

-(void)openAnimated:(BOOL)animated {

    CGRect frame = self.drawer.frame, frameBottom = self.drawerBottom.frame;
    frame.size.height = 300.0;
    frameBottom.size.height = 237.0;

    if (animated && !isRotating) {

        isRotating = YES;

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            self.chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
            self.drawerHeight.constant = frame.size.height;
            self.drawer.frame = frame;
            self.drawerBottom.frame = frameBottom;
        } completion:^(BOOL finished) {
            isRotating = NO;
            self.isOpen = YES;
            self.drawerBottom.hidden = NO;
        }];

    } else {
        [self.chevron.layer removeAllAnimations];
        self.chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
        self.drawerHeight.constant = frame.size.height;
        self.drawer.frame = frame;
        isRotating = NO;
        self.isOpen = YES;
        self.drawerBottom.hidden = NO;
        self.drawerBottom.frame = frameBottom;
    }
}

@end

@implementation WalletsTxsHelperBase
// auto-sythesized properties
@end

@implementation WalletsTxCell
// auto-sythesized properties

- (void) setDesc:(UILabel *)desc {
    if (_desc == desc) return;
    if (_desc) {
        [_desc removeObserver:self forKeyPath:@"text"];
    }
    _desc = desc;
    if (_desc) {
        [_desc addObserver:self forKeyPath:@"text" options:NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld|NSKeyValueObservingOptionInitial  context:NULL];
    }
}
- (void) polishLayout {
    CGFloat delta = _desc.text.length > 0 ? 9.0 : 0.0;

    self.amtCS.constant = 22.0 - delta;
    self.amtTitCS.constant = 24.0 - delta;
    self.dateCS.constant = 23.0 - delta;
    self.descCS.constant = 0.0 + delta;
    [self layoutIfNeeded];
}

- (void) observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary<NSKeyValueChangeKey,id> *)change context:(void *)context {
    if ([keyPath isEqualToString:@"text"] && object == _desc) {
        [self polishLayout];
    }
}
@end
