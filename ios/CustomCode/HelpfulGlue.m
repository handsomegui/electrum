//
//  HelpfulGlue.m
//  Electron-Cash
//
//  Created by calin on 2/23/18.
//  Copyright © 2018 Calin Culianu. MIT License
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <Python.h>
#include <dispatch/dispatch.h>
#import <CoreGraphics/CoreGraphics.h>

@interface HelpfulGlue : NSObject {
}
@end

typedef void(^VoidBlock)(void);

@implementation HelpfulGlue
+ (void) NSLogString:(NSString *)string {
    NSLog(@"%@",string);
}

+ (void) performBlockInMainThread:(VoidBlock)block sync:(BOOL)sync {
    if (!block) return;
    if (sync) {
        if (NSThread.currentThread.isMainThread) {
            block();
        } else {
            dispatch_sync(dispatch_get_main_queue(), block);
        }
    } else {
        dispatch_async(dispatch_get_main_queue(), block);
    }
}

// workaround to UIColor expecting extended color space and Max giving me device color space.
// returns a UIColor specified by components in device color space!
+ (UIColor *) deviceColorWithRed:(CGFloat)red green:(CGFloat)green blue:(CGFloat)blue alpha:(CGFloat)alpha {
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
@end

