# This line needs to be here becasue the iOS main.m evaluates this script and looks for a
# Python class (that is bridged to ObjC) named "PythonAppDelegate", which gets the
# 'applicationDidFinishLaunchingWithOptions' call, which is really where we start the app.
import electroncash_gui.ios_native.appdelegate
from electroncash_gui.ios_native.uikit_bindings import *
import sys, os, ssl

if __name__ == '__main__':
    #
    # The below is very important to allow OpenSSL to do SSL connections on iOS without verifying certs.
    # If you take this out, blockchain_headers from http://bitcoincash.com will fail, and the
    # "downloading headers" thing will take ages.  So I left this in.
    # TODO: figure out how else to get the certs file into the libOpenSSl.a archive.
    #   - Calin May 24, 2018
    #
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): 
        ssl._create_default_https_context = ssl._create_unverified_context
        print("*** SSL *** Allow Unverfied Context: ENABLED! ;)")
    
    argc = c_int(len(sys.argv))
    argv = (c_char_p * (argc.value + 1))()
    for i,a in enumerate(sys.argv):
        argv[i] = c_char_p(a.encode('utf-8'))
    argv[-1] = 0
    
    #.argtypes = [c_int, POINTER(c_char_p), c_void_p, c_void_p]
    uikit.UIApplicationMain(argc, argv, None, ns_from_py("PythonAppDelegate").ptr)
    sys.exit(0) # ensure we don't end up back in obj-c
    # at this point process exits.. note that objc's auto-generated main.m invocation of UIApplicationMain will not end up being called!
