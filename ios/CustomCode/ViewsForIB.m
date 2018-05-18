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
    const BOOL rotateChevron = !self.chevron.animationImages.count;

    if (animated && !isRotating) {

        isRotating = YES;

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            if (rotateChevron)
                self.chevron.transform = CGAffineTransformIdentity;
            self.drawer.frame = frame;
            self.drawerHeight.constant = 63.0;
            self.drawerBottom.frame = frameBottom;
            self.drawerBottom.hidden = YES;
        } completion:^(BOOL finished) {
            isRotating = NO;
            self.isOpen = NO;
            if (!rotateChevron)
                self.chevron.image = self.chevron.animationImages.lastObject;
        }];

    } else {
        [self.chevron.layer removeAllAnimations];
        if (rotateChevron)
            self.chevron.transform = CGAffineTransformIdentity;
        else
            self.chevron.image = self.chevron.animationImages.lastObject;
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
    const BOOL rotateChevron = !self.chevron.animationImages.count;

    if (animated && !isRotating) {

        isRotating = YES;

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            if (rotateChevron)
                self.chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
            self.drawerHeight.constant = frame.size.height;
            self.drawer.frame = frame;
            self.drawerBottom.frame = frameBottom;
        } completion:^(BOOL finished) {
            isRotating = NO;
            self.isOpen = YES;
            self.drawerBottom.hidden = NO;
            if (!rotateChevron)
                self.chevron.image = self.chevron.animationImages.lastObject;
        }];

    } else {
        [self.chevron.layer removeAllAnimations];
        if (rotateChevron)
            self.chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
        else
            self.chevron.image = self.chevron.animationImages.lastObject;
        self.drawerHeight.constant = frame.size.height;
        self.drawer.frame = frame;
        isRotating = NO;
        self.isOpen = YES;
        self.drawerBottom.hidden = NO;
        self.drawerBottom.frame = frameBottom;
    }
}

@end

@implementation TxHistoryHelperBase
// auto-sythesized properties
@end

@implementation TxHistoryCell
// auto-sythesized properties

- (void) dealloc {
    // this is required to make sure our KVO observing gets uninstalled!
    self.desc = nil;
}

- (void) setDesc:(UILabel *)desc {
    if (_desc == desc) return;
    if (_desc) {
        [_desc removeObserver:self forKeyPath:@"text"];
        [_desc removeObserver:self forKeyPath:@"attributedText"];
    }
    _desc = desc;
    if (_desc) {
        [_desc addObserver:self forKeyPath:@"text" options:NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld|NSKeyValueObservingOptionInitial  context:NULL];
        [_desc addObserver:self forKeyPath:@"attributedText" options:NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld|NSKeyValueObservingOptionInitial  context:NULL];
    }
}
- (void) polishLayout:(BOOL)isAttributed {
    CGFloat delta = (isAttributed ? _desc.attributedText.string : _desc.text).length > 0 ? 9.0 : 0.0;

    self.amtCS.constant = 17.0 - delta;
    self.amtTitCS.constant = 19.0 - delta;
    self.dateCS.constant = 18.0 - delta;
    self.descCS.constant = 0.0 + floor(delta/2.0);
    [self layoutIfNeeded];
}

- (void) observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary<NSKeyValueChangeKey,id> *)change context:(void *)context {
    BOOL isAttributed = [keyPath isEqualToString:@"attributedText"];
    if ( (isAttributed || [keyPath isEqualToString:@"text"]) && object == _desc) {
        [self polishLayout:isAttributed];
    }
}

@end

@implementation ReqTVDBase
// auto-synthesized properties generated by compiler here...
@end

@implementation RequestListCell
// auto-sythesized properties

- (void) dealloc {
    // this is required to make sure our KVO observing gets uninstalled!
    self.desc = nil;
}

- (void) setDesc:(UILabel *)desc {
    if (_desc == desc) return;
    if (_desc) {
        [_desc removeObserver:self forKeyPath:@"text"];
        [_desc removeObserver:self forKeyPath:@"attributedText"];
    }
    _desc = desc;
    if (_desc) {
        [_desc addObserver:self forKeyPath:@"text" options:NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld|NSKeyValueObservingOptionInitial  context:NULL];
        [_desc addObserver:self forKeyPath:@"attributedText" options:NSKeyValueObservingOptionNew|NSKeyValueObservingOptionOld|NSKeyValueObservingOptionInitial  context:NULL];
    }
}
- (void) polishLayout:(BOOL)isAttributed {
    CGFloat delta = (isAttributed ? _desc.attributedText.string : _desc.text).length > 0 ? 7.5 : 0.0;

    self.addressTitCS.constant = 21.0 - delta;
    [self layoutIfNeeded];
}

- (void) observeValueForKeyPath:(NSString *)keyPath ofObject:(id)object change:(NSDictionary<NSKeyValueChangeKey,id> *)change context:(void *)context {
    BOOL isAttributed = [keyPath isEqualToString:@"attributedText"];
    if ( (isAttributed || [keyPath isEqualToString:@"text"]) && object == _desc) {
        [self polishLayout:isAttributed];
    }
}
@end

@implementation ContactsVCBase
// auto synthesized properties
@end

@implementation ContactsCell
// auto synthesized properties
@end
