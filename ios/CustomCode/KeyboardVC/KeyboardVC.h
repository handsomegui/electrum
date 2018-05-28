//
//  KeyboardVC.h
//  tskbd
//
//  Created by calin on 5/27/18.
//  Copyright © 2018 c3-soft.com. All rights reserved.
//

#import <UIKit/UIKit.h>

/**
 * Apple iOS keyboard work-alike developed for things like typing in wallet seeds. Use the keyCallback to forward input
 * over to your UITextView and UITextField, or assign your uitextview/field to .textInput for this class to handle
 * everything for you.
 */
@interface KeyboardVC : UIViewController
@property (nonatomic, readonly, class) CGSize preferredSize;
@property (nonatomic, readonly) CGSize keySize; ///< various sizes of GUI elements.  These are hard-coded for now.
@property (nonatomic) CGFloat hpad, vpad, hmargin, vmargin; ///< the margins to use in-between keys and around them, etc.

@property (nonatomic) BOOL blockPasting; ///< defaults to YES. IFF yes and this is the delegate of the TextView/TextField, attempt to block pasting of text.
@property (nonatomic) BOOL blockSelecting; ///< defaults to YES. IFF yes and this is the delegate of the TextView/TextField, attempt to selecting of text.
@property (nonatomic) BOOL lowerCase; ///< defaults to NO. If YES, will use lowercase letters on the keyboard
#pragma mark Main Usage Mechanisms

@property (nonatomic, copy) void (^keyCallback)(NSString *key);
@property (nonatomic, readonly) NSString *backSpace; ///< this is sent to callback when user hits backspace

@property (nonatomic, weak) IBOutlet id<UITextInput> textInput; ///< attach a UITextField or UITextView here if you like, or use the keyCallback if you prefer that method. Attaching a UITextField here will make everything work automatically

#pragma mark Enabling/Disabling individual keys

@property (nonatomic, readonly) NSArray<NSString *> *allKeys, *disabledKeys;

- (BOOL) isKeyDisabled:(NSString *)key;
- (void) setKey:(NSString *)key disabled:(BOOL)disabled;
@end


@interface FakeInputView : UIView<UIInputViewAudioFeedback>
/// this is required to get the clicks working.
- (BOOL) enableInputClicksWhenVisible;

/// optionally attach this fake input view to your UITextView/UITextField when using the KeyboardVC in "statically-laid-out" mode to get key clicks!
+ (instancetype) fakeInputView;
@end
