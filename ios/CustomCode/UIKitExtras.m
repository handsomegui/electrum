//
//  UIViewExtras.m
//  AppVault
//
//  Created by calin on 9/29/09.
//  Copyright 2009 Calin Culianu <calin.culianu@gmail.com>. MIT License.
//

#import "UIKitExtras.h"
#import <QuartzCore/QuartzCore.h>
#include <stdlib.h>
#import <objc/runtime.h>
#import <CoreGraphics/CoreGraphics.h>

#define kGuiAnimDur 0.3 /* in seconds */

static double Rand(double lo, double hi)
{
    static const double ARC4RMAX = 4294967295.;
    const double r = arc4random();
    return (double)( ((double)(hi-lo)) * (r/ARC4RMAX) + (double)lo );
}

@interface AnimShakeState : NSObject {
	__weak UIView *view;
	CGPoint origCenter;
	NSUInteger nShakes;
	CGFloat speed, displacement, randPerturbAmount;
}
@property (nonatomic, weak) UIView *view;
@property (nonatomic, assign) CGPoint origCenter;
@property (nonatomic, assign) NSUInteger nShakes;
@property (nonatomic, assign) CGFloat speed;
@property (nonatomic, assign) CGFloat displacement;
@property (nonatomic, assign) CGFloat randPerturbAmount;
- (void) willStart;
- (void) didStop;
- (void) animStep;
@end

@implementation UIView (AnimExtras)

// property accessor
- (BOOL) hasAnimations { return [self.layer animationKeys].count; }

- (void) animExtrasAnimationDidStopSelector:(NSString *)animId finished:(NSNumber *)finished context:(void *)context {
    if (context) {
        NSInvocation *inv = (__bridge_transfer NSInvocation *)context; // implicit release
        id selfarg = nil;
        void *slf = NULL;
        if (inv.methodSignature.numberOfArguments > 2) {
            [inv getArgument:&slf atIndex:2];
            selfarg = (__bridge_transfer id)slf; // implicit release to match implicit retain when inv was created
        }
        [inv invoke];
    }
}

- (void) animExtrasAnimationDidStopSelector_SlideOut:(NSString *)animId finished:(NSNumber *)finished context:(void *)context {
    if (context) {
        NSInvocation *inv = (__bridge_transfer NSInvocation *)context; // implicit release
        id selfarg = nil;
        void *slf = NULL;
        if (inv.methodSignature.numberOfArguments > 2) {
            [inv getArgument:&slf atIndex:2];
            selfarg = (__bridge_transfer id)slf; // implicit release to match implicit retain when inv was created
        }
		[inv invoke];
        [self removeFromSuperview];
	}
}

/// adds this view to parent view, and slides it into existence
- (void) modalSlideFromBottomIntoView:(UIView *)parentView {	[self modalSlideFromBottomIntoView:parentView target:nil selector:NULL]; }

/// like above but with callback when done. callback takes 1 argument, the view itself.
- (void) modalSlideFromBottomIntoView:(UIView *)parentView target:(id)target selector:(SEL)selector {
	CGRect frame = self.frame;
	frame.origin.y = parentView.frame.size.height;
	frame.origin.x = round((parentView.frame.size.width - self.bounds.size.width) / 2.);
	[parentView addSubview:self];
	self.hidden = NO;
	self.frame = frame;
	void *context = NULL;
	if (target && selector) {
		NSMethodSignature *ms;
        NSInvocation *inv = [NSInvocation invocationWithMethodSignature:ms=[target methodSignatureForSelector:selector]];
		[inv setTarget:target];
		[inv setSelector:selector];
        if ([ms numberOfArguments] > 2)	{
            void *selfarg = (__bridge_retained void *)self; // implicit retain here
            [inv setArgument:&selfarg atIndex:2];
        }
        [inv retainArguments];
		context = (__bridge_retained void *)inv; // implicit retain
	}
	[UIView beginAnimations:[NSString stringWithFormat:@"AnimModalSlide1:%@",self] context:context];
	[UIView setAnimationDuration:kGuiAnimDur];
	if (context) {
		[UIView setAnimationDelegate:self];
		[UIView setAnimationDidStopSelector:@selector(animExtrasAnimationDidStopSelector:finished:context:)];
	} else {
		[UIView setAnimationDelegate:nil];
	}
	frame.origin.y = parentView.bounds.size.height-frame.size.height;
	self.frame = frame;
	[UIView commitAnimations];
	[self becomeFirstResponder];
}

/// slides the view out the bottom and removes it from parent when animation is done
- (void) modalSlideOutToBottom { [self modalSlideOutToBottomWithTarget:nil selector:nil]; }
/// same as above but also with callback when done.  callback take 1 argument, the UIView itself
- (void) modalSlideOutToBottomWithTarget:(id)target selector:(SEL)selector {
	if ([self isFirstResponder])	[self resignFirstResponder];
	CGRect frame = self.frame, parentFrame = [self superview].frame;
	self.hidden = NO;
	void *context = NULL;
	if (target && selector) {
		//[target retain];
		NSMethodSignature *ms;
        NSInvocation *inv = [NSInvocation invocationWithMethodSignature:ms=[target methodSignatureForSelector:selector]];
		[inv setTarget:target];
		[inv setSelector:selector];
        if ([ms numberOfArguments] > 2) {
            void *selfarg = (__bridge_retained void *)self; // implicit retain here
            [inv setArgument:&selfarg atIndex:2];
        }
        [inv retainArguments];
		context = (__bridge_retained void *)inv; // implicit retain
	}
	[UIView beginAnimations:[NSString stringWithFormat:@"AnimModalSlide2:%@",self] context:context];
	[UIView setAnimationDuration:kGuiAnimDur];
	[UIView setAnimationDelegate:self];
	[UIView setAnimationDidStopSelector:@selector(animExtrasAnimationDidStopSelector_SlideOut:finished:context:)];
	frame.origin.y = parentFrame.size.height;
	self.frame = frame;
	[UIView commitAnimations];	
}

- (void)fadeDidStop:(NSString *)animationID finished:(NSNumber *)finished context:(void *)context {
	if ([finished boolValue]) {
		UIView *other = (__bridge_transfer UIView *)context;
		other.hidden = YES;
	}
}

/// Fades receiver in, fading out `otherView'.  Hides `otherView' when done
- (void) fadeInWhileFadingOutOther:(UIView *)other {
	self.hidden = NO;
	other.hidden = NO;
	self.alpha = 0.;
	other.alpha = 1.;
	[UIView beginAnimations:nil context:(__bridge_retained void *)other];
	[UIView setAnimationDelegate:self];
	[UIView setAnimationDidStopSelector:@selector(fadeDidStop:finished:context:)];
	[UIView setAnimationDuration:kGuiAnimDur*2.];
	self.alpha = 1.;
	other.alpha = 0.;
	[UIView commitAnimations];
}



/// Animate oscillate action -- a good default speed is 10.0
- (void) animateShake:(NSUInteger)nShakes speed:(CGFloat)speed displacement:(CGFloat)disp randPerturbAmount:(CGFloat)pert {
	AnimShakeState *ass = [AnimShakeState new];
	ass.nShakes = nShakes;
	ass.speed = speed;
	ass.randPerturbAmount = pert;
	ass.view = self;
	ass.origCenter = self.center;
	ass.displacement = disp;
	[ass animStep];
}

/// Renders this entire view to an image, returns the autoreleased image
- (UIImage *) renderToImage { return [self renderToImage:self.bounds]; }	
/// Same as above, but just for a subrect of the view
- (UIImage *) renderToImage:(CGRect)rectInView {
	const CGRect bounds = self.bounds;
	rectInView = CGRectIntersection(bounds,rectInView); // only render up to the view's bounds!
	if (CGRectIsEmpty(rectInView)) return nil;
	UIGraphicsBeginImageContext(bounds.size);
	CGContextRef ctx = UIGraphicsGetCurrentContext();
	CGContextClipToRect(ctx, rectInView);
	CGContextTranslateCTM(ctx, 0, bounds.size.height);
	CGContextScaleCTM(ctx, 1.0, -1.0); // flip it since it gets drawn upside-down
	[self.layer renderInContext:ctx];
	UIImage *img1 = UIGraphicsGetImageFromCurrentImageContext();
	UIGraphicsEndImageContext();

	if (CGRectEqualToRect(bounds,rectInView)) return img1;
	// now, trim the image to the actual contents
	UIGraphicsBeginImageContext(rectInView.size);
	ctx = UIGraphicsGetCurrentContext();
	CGContextClipToRect(ctx, CGRectMake(0,0,rectInView.size.width,rectInView.size.height));
	CGRect r = CGRectMake(-rectInView.origin.x, -rectInView.origin.y, bounds.size.width, bounds.size.height);
	CGContextDrawImage(ctx, r, img1.CGImage);
	UIImage *img2 = UIGraphicsGetImageFromCurrentImageContext();
	UIGraphicsEndImageContext();
	return img2;
}

-(void) backgroundColorAnimationFromColor:(UIColor *)startColor toColor:(UIColor *)destColor duration:(CGFloat)duration reverses:(BOOL)reverses completion:(void(^)(void))completion
{
    [self.layer removeAllAnimations];
    const BOOL uilabelHack = [self isKindOfClass:[UILabel class]];
    if (uilabelHack) {
        self.backgroundColor = UIColor.clearColor;
        self.layer.backgroundColor = startColor.CGColor;
    } else
        self.backgroundColor = startColor;
    if (reverses) duration /= 2.0;

    [UIView animateWithDuration:duration delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
        if (uilabelHack) {
            self.layer.backgroundColor = destColor.CGColor;
        } else
            self.backgroundColor = destColor;
    } completion:^(BOOL finished) {
        if (!finished) return;
        if (reverses) {
            [self.layer removeAllAnimations];
            if (uilabelHack) {
                self.layer.backgroundColor = destColor.CGColor;
            } else
                self.backgroundColor = destColor;
            [UIView animateWithDuration:duration delay:0.0 options: UIViewAnimationOptionAllowUserInteraction |UIViewAnimationOptionCurveLinear animations:^{
                if (uilabelHack) {
                    self.layer.backgroundColor = startColor.CGColor;
                } else
                    self.backgroundColor = startColor;
            } completion:^(BOOL finished2) {
                if (!finished2) return;
                [self.layer removeAllAnimations];
                self.backgroundColor = startColor;
                if (completion) completion();
            }];
        } else {
            self.backgroundColor = destColor;
            if (completion) completion();
        }
    }];
}

-(void) backgroundColorAnimationToColor:(UIColor *)destColor
                               duration:(CGFloat)duration
                               reverses:(BOOL)reverses
                             completion:(void(^)(void))completion {
    return [self backgroundColorAnimationFromColor:self.backgroundColor toColor:destColor duration:duration reverses:reverses completion:completion];
}
@end

@implementation UILabel(MiscEffects)
-(void) textColorAnimationFromColor:(UIColor *)startColor toColor:(UIColor *)destColor duration:(CGFloat)duration reverses:(BOOL)reverses completion:(void(^)(void))completion {
    [self.layer removeAllAnimations];
    if (reverses) duration /= 2.0;
    self.textColor = startColor;
    [UIView transitionWithView:self duration:duration options:UIViewAnimationOptionTransitionCrossDissolve animations:^{
        self.textColor = destColor;
    } completion:^(BOOL finished) {
        if (!finished) return;
        if (reverses) {
            [self.layer removeAllAnimations];
            self.textColor = destColor;
            [UIView transitionWithView:self duration:duration options:UIViewAnimationOptionTransitionCrossDissolve animations:^{
                self.textColor = startColor;
            } completion:^(BOOL finished2) {
                if (!finished2) return;
                self.textColor = startColor;
                if (completion) completion();
            }];
        } else {
            self.textColor = destColor;
            if (completion) completion();
        }
    }];
}

-(void) textColorAnimationToColor:(UIColor *)destColor
                         duration:(CGFloat)duration
                         reverses:(BOOL)reverses
                       completion:(void(^)(void))completion {
    return [self textColorAnimationFromColor:self.textColor toColor:destColor duration:duration reverses:reverses completion:completion];
}
@end


@implementation AnimShakeState
@synthesize view,origCenter,nShakes,speed,displacement,randPerturbAmount;
- (void) animStep {
	if (nShakes > 0) {
		[UIView beginAnimations:nil context:NULL];
		[UIView setAnimationDuration:1./speed];
		[UIView setAnimationDelegate:self];
		[UIView setAnimationWillStartSelector:@selector(willStart)];
		[UIView setAnimationDidStopSelector:@selector(didStop)];
		[UIView setAnimationCurve:UIViewAnimationCurveLinear];
        const CGFloat disp = displacement + (randPerturbAmount > 0. ? Rand(-fabs(randPerturbAmount),fabs(randPerturbAmount)) : 0.);
		CGPoint c = view.center;
		if (c.x < origCenter.x) {
			c.x = origCenter.x + disp;
		} else {
			c.x = origCenter.x - disp;			
		}
		view.center = c;
		[UIView commitAnimations];
	}
}
- (void) willStart {
	--nShakes;
}

- (void) didStop {
	if (nShakes > 0)
		[self animStep];
	else {
		view.center = origCenter;
//		[self autorelease];
	}
}
@end


@implementation UIControl (UIControlBlockAction)

static long UIButtonBlockKey = 0xb10cb10c;
- (void)callActionBlock:(id)sender {
    ActionBlock block = (ActionBlock)objc_getAssociatedObject(self, &UIButtonBlockKey);
    if (block) {
        block(sender);
    }
}

- (void)handleControlEvent:(UIControlEvents)event withBlock:(ActionBlock)block {
    objc_setAssociatedObject(self, &UIButtonBlockKey, block, OBJC_ASSOCIATION_COPY);
    if (block)
        [self addTarget:self action:@selector(callActionBlock:) forControlEvents:event];
    else
        [self removeTarget:self action:@selector(callActionBlock:) forControlEvents:event];
}

@end

// UIView+ViewRecursion.m
@implementation UIView (ViewRecursion)
- (NSArray * )allSubviewsRecursively
{
    NSMutableArray *ret = [NSMutableArray new];
    NSArray *svs = self.subviews;
    for (UIView *sv in svs) {
        [ret addObject:sv];
        [ret addObjectsFromArray:[sv allSubviewsRecursively]];
    }
    return ret;
}
@end


@implementation UIView (Mogrification)
- (void) affineScaleX:(CGFloat)scaleX scaleY:(CGFloat)scaleY  {
    self.transform = CGAffineTransformMakeScale(scaleX, scaleY);
}
- (void) affineScale:(CGPoint)xyScale { [self affineScaleX:xyScale.x scaleY:xyScale.y]; }
@end

@implementation ForwardingDelegate
@synthesize fwdDelegate;
- (instancetype) initWithDelegate:(id<NSObject>)fwd {
    if (self = [super init]) {
        self.fwdDelegate = fwd;
    }
    return self;
}
- (BOOL)respondsToSelector:(SEL)aSelector
{
    if ([[self class] instancesRespondToSelector:aSelector]) {
        return YES;
    }
    return [self.fwdDelegate respondsToSelector:aSelector];
}

- (id)forwardingTargetForSelector:(SEL)aSelector
{
    return self.fwdDelegate;
}
@end

@implementation UILabel (TextKerning)
-(void) setText:(NSString *)text withKerning:(CGFloat)kerning
{
    if ([self respondsToSelector:@selector(setAttributedText:)])
    {
        NSMutableAttributedString *attributedString = [[NSMutableAttributedString alloc] initWithString:text];
        [attributedString addAttribute:NSKernAttributeName
                                 value:[NSNumber numberWithFloat:kerning]
                                 range:NSMakeRange(0, [text length])];
        [self setAttributedText:attributedString];
    }
    else
        [self setText:text];
}

-(void) setKerning:(CGFloat)kerning
{
    [self setText:self.text withKerning:kerning];
}
@end

@implementation UIColor (DeviceRGB)
+ (UIColor *) colorInDeviceRGBWithRed:(CGFloat)red green:(CGFloat)green blue:(CGFloat)blue alpha:(CGFloat)alpha {
    static CGColorSpaceRef cs = NULL;
    UIColor *ret = nil;
    if (!cs) cs = CGColorSpaceCreateDeviceRGB();
    CGFloat components[4] = {red, green, blue, alpha};
    CGColorRef cg = CGColorCreate(cs, components);
    if (cg) {
        ret = [UIColor colorWithCGColor:cg];
        CGColorRelease(cg);
    }
    return ret;
}
+ (UIColor *) colorInDeviceRGBWithHexString:(NSString *)nsstr {
    const char *s = nsstr.lowercaseString.UTF8String;
    CGFloat components[4] = { 0.0, 0.0, 0.0, 1.0};
    if (s) {
        char buf[3] = { 0, 0, 0};
        int bufct = 0, compct = 0;
        for ( ; *s && compct < 4; ++s) {
            if ( (*s >= '0' && *s <= '9') || (*s >= 'a' && *s <= 'f') ) {
                buf[bufct++] = *s;
            }
            if (bufct >= 2) {
                long l = strtol(buf, NULL, 16);
                components[compct++] = ((CGFloat)l) / 255.0;
                bufct = 0;
            }
        }
    }
    return [UIColor colorInDeviceRGBWithRed:components[0] green:components[1] blue:components[2] alpha:components[3]];
}
@end