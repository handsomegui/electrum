//
//  CCActivityIndicator.m
//
//  Created by Calin Culianu on 5/21/2018.
//  Copyright (C) 2018 Calin Culianu <calin.culianu@gmail.com>. MIT License.
//

#import <CoreGraphics/CoreGraphics.h>
#import "CCActivityIndicator.h"

@implementation CCActivityIndicator {
    CGFloat _alpha;
    NSTimer *_timer;
}
- (void) dealloc {
    [_timer invalidate];
    _timer = nil;
}
- (void)ccCommonInit {
    self.backgroundColor = UIColor.clearColor;
    self.opaque = NO;
    // below attempts to politely not overwrite any values set by Interface Builder
    static const CGFloat epsilon = 0.00001;
    if (_speed <= epsilon) self.speed = 1.0;
    if (_fps <= epsilon) self.fps = 25.0;
    if (!_color) self.color = UIColor.whiteColor;
}
- (instancetype)init { if ((self=[super init])) [self ccCommonInit]; return self;}
- (instancetype)initWithFrame:(CGRect)frame { if ((self=[super initWithFrame:frame])) [self ccCommonInit]; return self;}
- (instancetype)initWithCoder:(NSCoder *)coder { if ((self=[super initWithCoder:coder])) [self ccCommonInit]; return self; }
- (void)drawRect:(CGRect)rect
{

    const CGFloat height = MIN(CGRectGetHeight(rect), CGRectGetWidth(rect));

    CGFloat smallCircleHeight = height / 4.0f;
    if (smallCircleHeight < 6.0)
        smallCircleHeight = 6.0;

    const CGRect bigCircleRect = CGRectInset(rect, smallCircleHeight / 2.0f, smallCircleHeight / 2.0f);
    const CGFloat bigCircleRadius = MIN(CGRectGetHeight(bigCircleRect) / 2.0f, CGRectGetWidth(bigCircleRect) / 2.0f);

    const CGPoint rectCenter = CGPointMake(CGRectGetMidX(rect), CGRectGetMidY(rect));

    CGContextRef context = UIGraphicsGetCurrentContext();

    CGContextSetLineWidth(context, 2.0f);

    CGContextSetStrokeColorWithColor(context, _color.CGColor);
    CGContextAddEllipseInRect(context, bigCircleRect);
    CGContextStrokePath(context);

    CGContextSetFillColorWithColor(context, _color.CGColor);


    static const NSUInteger kNumCircles = 3u;
    static const CGFloat kAlphaMuls[kNumCircles] = {0.33, 1.33, 1.66};
    static const CGFloat kSizeMuls[kNumCircles] = {1.0, 0.75, 0.66};
    static const CGFloat kClamp = (M_PI * 2.0)*1e3;
    if (_alpha > kClamp)
        // clamp alpha to some fixed high value to avoid floating point degeneration
        _alpha = _alpha - kClamp;
    CGFloat alpha = _alpha;

    for (NSUInteger i = 0; i < kNumCircles; ++i)
    {
        const CGFloat myalpha = alpha*kAlphaMuls[i];
        const CGFloat myheight = smallCircleHeight*kSizeMuls[i];
        CGPoint smallCircleCenter = CGPointMake(rectCenter.x  + bigCircleRadius * cos(myalpha) - myheight/2.0f , rectCenter.y + bigCircleRadius * sin(myalpha) - myheight / 2.0f );
        CGRect smallCircleRect = CGRectMake(smallCircleCenter.x,smallCircleCenter.y,myheight,myheight);

        CGContextAddEllipseInRect(context, smallCircleRect);
        CGContextFillPath(context);
        alpha += M_PI / (kNumCircles / 2.0f);
    }
}

- (void) setAnimating:(BOOL)b {
    if (!!_animating == !!b) return;
    _animating = b;
    __weak CCActivityIndicator * weakSelf = self;
    if (_animating) {
        CGFloat fps = self.fps;
        if (fps < 0.25) fps = 0.25;
        if (fps > 60.0) fps = 60.0;
        _timer = [NSTimer scheduledTimerWithTimeInterval:1.0/fps repeats:YES block:^(NSTimer *t) {
            __strong CCActivityIndicator *strongSelf = weakSelf;
            if (strongSelf) {
                strongSelf->_alpha += (5.0 * strongSelf->_speed) / fps;
                //NSLog(@"Timer called for: %@", weakSelf);
                [strongSelf setNeedsDisplay];
            }
        }];
    } else {
        [_timer invalidate];
        _timer = nil;
    }
}

@end


