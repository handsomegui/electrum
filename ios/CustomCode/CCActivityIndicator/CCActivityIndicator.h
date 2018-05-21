//
//  CCActivityIndicator.h
//
//  Created by Calin Culianu on 5/21/2018.
//  Copyright (C) 2018 Calin Culianu <calin.culianu@gmail.com>. MIT License.
//

#import <UIKit/UIKit.h>

/**
 * CCActivityIndicator
 *
 * Developed for Electron Cash.  This is another take on the UIActivityIndicator view.  It's more-or-less a
 * drop-in replacement for it.  But instead of the spinny rectangle-flower thing, it is a bunch of 'electrons'
 * in an obital at different speeds.
 */
@interface CCActivityIndicator : UIView
@property (nonatomic, copy) UIColor *color;
@property (nonatomic, assign) BOOL animating;
@property (nonatomic, assign) CGFloat fps; //< defaults to 25.0. Just how much CPU do you want to devote to this view? :) Note setting the value to negative or 0.0 will result in undefined behavior.
@property (nonatomic, assign) CGFloat speed; //< defaults to 1.0.  Set it to negative for retrograde motion, or >1.0 to speed up the animation, or <1.0 to slow it down
@property (nonatomic, assign) CGFloat lineWidth; //< defaults to 0.0, which means auto (based on size of View).  Otherwise, if specified, it's the thickness of the stroked circle's line.
@end

