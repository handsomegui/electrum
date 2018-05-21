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


@implementation WalletsDrawerVCBase {
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

@implementation ContactDetailVCBase
// auto synthesized properties
@end

@implementation ComboDrawerPicker {
    BOOL _inInit, _initted, _isRotating;
    __strong NSMutableArray<UIImage *> *_chevronImages, *_chevronImagesReversed;
    __strong UIImage *_bluechk, *_blankimg;
    CGFloat _savedBottomHeight;
}

- (void) commonInit {
    if (_initted) return;
    _inInit = YES;
    if (!_colorTitle) self.colorTitle = UIColor.grayColor;
    if (!_colorTitle2) self.colorTitle2 = UIColor.blueColor;
    if (!_colorItems) self.colorItems = UIColor.blackColor;
    _lmarginCS.active = NO;
    _chevronImages = [NSMutableArray arrayWithCapacity:6];
    _chevronImagesReversed = [NSMutableArray arrayWithCapacity:6];
    for (int i = 0; i < 6; ++i) {
        [_chevronImages addObject:[UIImage imageNamed:[NSString stringWithFormat:@"chevron_0000%u",(unsigned)i]]];
        [_chevronImagesReversed insertObject:_chevronImages[i] atIndex:0];
    }
    _bluechk = [UIImage imageNamed:@"bluechk"];
    { // create the blank image
        CGSize size = _bluechk.size;
        UIGraphicsBeginImageContextWithOptions(size, NO, _bluechk.scale);
        [[UIColor clearColor] setFill];
        UIRectFill(CGRectMake(0, 0, size.width, size.height));
        _blankimg = UIGraphicsGetImageFromCurrentImageContext();
        UIGraphicsEndImageContext();
    }
    _chevron.animationImages = _chevronImages;
    _chevron.highlightedAnimationImages = _chevronImagesReversed;
    _chevron.highlightedImage = _chevronImagesReversed[0];
    _chevron.image = _chevronImages[0];
    self.topTitle = @"Title";
    self.items = @[@"Item 1", @"Item 2", @"Item 3", @"Item 4"];
    _savedBottomHeight = _bottomHeightCS.constant;
    if (!_opened) {
        _bottomHeightCS.constant = 0;
    }
    _chevron.highlighted = _opened;
    _inInit = NO;
    _initted = YES;
}
- (void)viewDidLoad { [super viewDidLoad]; [self commonInit]; }
- (void)viewWillAppear:(BOOL)animated {
    [super viewWillAppear:animated];
    [self redoTitle];
    [_tv reloadData];
}
- (void) redoTitle {
    if (_selection >= _items.count || _inInit) return;
    // TODO: use NSAttributedString here..
    NSMutableAttributedString *ats =
    [[NSMutableAttributedString alloc] initWithString:_topTitle
                                           attributes:@{
                                                         NSFontAttributeName : [UIFont systemFontOfSize:12.0],
                                                         NSForegroundColorAttributeName : self.colorTitle
                                                         }
     ];
    [ats appendAttributedString:
     [[NSMutableAttributedString alloc] initWithString:[NSString stringWithFormat:@"  %@",_items[_selection]]
                                            attributes:@{
                                                         NSFontAttributeName : [UIFont systemFontOfSize:14.0 weight:UIFontWeightBold],
                                                         NSForegroundColorAttributeName : self.colorTitle2

                                                         }
      ]];

    _titLbl.attributedText = ats;
}
// property override
- (void) setTopTitle:(NSString *)topTitle {
    _topTitle = [topTitle copy];
    [self redoTitle];
}
- (void) setItems:(NSArray<NSString *> *)items {
    _items = [items copy];
    if (_selection >= _items.count)
        self.selection = 0; // implicitly calls redoTitle
    else
        [self redoTitle];
    if (!_inInit) [_tv reloadData];
}
- (void) setFlushLeft:(BOOL)flushLeft {
    if (!!_flushLeft == flushLeft) return;
    _flushLeft = flushLeft;
    if (_flushLeft) {
        _lmarginCS.active = YES;
        _rmarginCS.active = NO;
    } else {
        _lmarginCS.active = NO;
        _rmarginCS.active = YES;
    }
}

- (void) setSelection:(NSUInteger)selection {
    if (_selection == selection || selection > _items.count) return;
    _selection = selection;
    if (!_inInit) {
        [self redoTitle];
        [_tv reloadData];
    }
}

- (void) setColorItems:(UIColor *)colorItems {
    _colorItems = [colorItems copy];
    if (!_inInit) [_tv reloadData];
}

- (void) setColorTitle:(UIColor *)colorTitle {
    _colorTitle = [colorTitle copy];
    if (!_inInit) [self redoTitle];
}


- (void) setColorTitle2:(UIColor *)colorTitle2 {
    _colorTitle2 = [colorTitle2 copy];
    if (!_inInit) [self redoTitle];
}

- (void) setOpened:(BOOL)opened {
    if (!!_opened == !!opened) return;
    if (_initted) {
        if (opened) [self openAnimated:YES];
        else [self closeAnimated:YES];
    } else
        _opened = opened;
}

- (void) toggleOpen {
    self.opened = !_opened;
}

-(void)openAnimated:(BOOL)animated  {
    const BOOL rotateChevron = !_chevron.animationImages.count;

    _opened = YES;
    if (animated && !_isRotating) {

        _isRotating = YES;


        if (!rotateChevron) {
            _chevron.animationDuration = 0.2;
            _chevron.highlighted = NO;
            [_chevron startAnimating];
        }

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            if (rotateChevron)
                _chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
            CGRect frame = _bottomView.frame;
            frame.size.height = _savedBottomHeight;
            _bottomView.frame = frame;
        } completion:^(BOOL finished) {
            _bottomHeightCS.constant = _savedBottomHeight;
            _isRotating = NO;
            _opened = YES;
            if (!rotateChevron) {
                [_chevron stopAnimating];
                _chevron.highlighted = YES;
            }
            if (finished && _openClosedBlock) _openClosedBlock(YES);
        }];

    } else {
        [_chevron.layer removeAllAnimations];
        if (rotateChevron)
            _chevron.transform = CGAffineTransformMakeRotation(DEGREES_TO_RADIANS(179.9f));
        else {
            [_chevron stopAnimating];
            _chevron.highlighted = YES;
        }
        _bottomHeightCS.constant = _savedBottomHeight;
        _isRotating = NO;
        _opened = YES;
        if (_openClosedBlock) _openClosedBlock(YES);
    }
}

-(void)closeAnimated:(BOOL)animated {
    const BOOL rotateChevron = !_chevron.highlightedAnimationImages.count;

    _opened = NO;
    if (animated && !_isRotating) {

        _isRotating = YES;


        if (!rotateChevron) {
            _chevron.animationDuration = 0.2;
            _chevron.highlighted = YES;
            [_chevron startAnimating];
        }

        [UIView animateWithDuration:0.2 delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
            if (rotateChevron)
                _chevron.transform = CGAffineTransformIdentity;
            CGRect frame = _bottomView.frame;
            frame.size.height = 0;
            _bottomView.frame = frame;
            _bottomHeightCS.constant = 0.;
        } completion:^(BOOL finished) {
            _bottomHeightCS.constant = 0;
            _isRotating = NO;
            _opened = NO;
            if (!rotateChevron) {
                [_chevron stopAnimating];
                _chevron.highlighted = NO;
            }
            if (finished && _openClosedBlock) _openClosedBlock(NO);
        }];

    } else {
        [_chevron.layer removeAllAnimations];
        if (rotateChevron)
            _chevron.transform = CGAffineTransformIdentity;
        else {
            [_chevron stopAnimating];
            _chevron.highlighted = NO;
        }
        _bottomHeightCS.constant = 0;
        _isRotating = NO;
        _opened = NO;
        if (_openClosedBlock) _openClosedBlock(NO);
    }
}

- (NSInteger) numberOfSectionsInTableView:(UITableView *)tv { return 1; }
- (NSInteger) tableView:(UITableView *)tv numberOfRowsInSection:(NSInteger)section {
    return _inInit ? 0 : _items.count;
}
- (UITableViewCell *) tableView:(UITableView *)tv cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    UITableViewCell *cell = [tv dequeueReusableCellWithIdentifier:@"Cell"];
    if (!cell) {
        cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:@"Cell"];
    }
    if (indexPath.row < _items.count) {
        cell.textLabel.text = _items[indexPath.row];
        cell.textLabel.textColor = _colorItems;
        cell.textLabel.font = [UIFont systemFontOfSize:14.0];
        cell.imageView.image = indexPath.row == _selection ? _bluechk : _blankimg;
    }
    return cell;
}
- (void) tableView:(UITableView *)tv didSelectRowAtIndexPath:(nonnull NSIndexPath *)indexPath {
    [tv deselectRowAtIndexPath:indexPath animated:YES];
    // Delay 0.1 seconds so deselect animation can play, then select it
    __weak ComboDrawerPicker *weakSelf = self;
    const NSInteger sel = indexPath.row; // to not keep the indexPath object alive longer than we need to
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, (int64_t)(0.1 * NSEC_PER_SEC)), dispatch_get_main_queue(), ^{
        weakSelf.selection = sel;
        if (weakSelf.selectedBlock) weakSelf.selectedBlock(sel);
    });
}
- (IBAction) tappedOutside:(UIGestureRecognizer *)gr {
    if (_backgroundTappedBlock) {
        CGPoint p = [gr locationInView:self.view];
        _backgroundTappedBlock(p);
    }
}
- (IBAction) tappedControl {
    if (_autoOpenCloseOnTap) [self toggleOpen];
    if (_controlTappedBlock) _controlTappedBlock();
}
@end
