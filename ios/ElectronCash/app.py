#
# This file is:
#     Copyright (C) 2018 Calin Culianu <calin.culianu@gmail.com>
#
# MIT License
#
import sys, os
from electroncash import daemon
from electroncash.util import set_verbosity
from electroncash_gui.ios_native import ElectrumGui
from electroncash_gui.ios_native.utils import get_user_dir, call_later
from electroncash.networks import NetworkConstants
from electroncash.simple_config import SimpleConfig
from electroncash_gui.ios_native.uikit_bindings import *

def main():
    print("HomeDir from ObjC = '%s'"%get_user_dir())

    script_dir = os.path.dirname(os.path.realpath(__file__))
    is_bundle = getattr(sys, 'frozen', False)
    print("script_dir = '%s'\nis_bunde = %s"%(script_dir, str(is_bundle)))

    # config is an object passed to the various constructors (wallet, interface, gui)
    config_options = {
            'verbose': True,
            'cmd': 'gui',
            'gui': 'ios_native',
    }

    config_options['cwd'] = os.getcwd()

    set_verbosity(config_options.get('verbose'))

    for k,v in config_options.items():
        print("config[%s] = %s"%(str(k),str(v)))

    config = SimpleConfig(config_options,read_user_dir_function=get_user_dir)

    try:
        # Force remove of lock file so the code below cuts to the chase and starts a new daemon without
        # uselessly trying to connect to one that doesn't exist anyway.
        # (We're guaranteed only 1 instance of this app by iOS regardless)
        os.remove(daemon.get_lockfile(config))
        print("Pre-existing 'daemon' lock-file removed!")
    except:
        pass

    fd, server = daemon.get_fd_or_server(config)
    if fd is not None:
        d = daemon.Daemon(config, fd, True)
        gui = ElectrumGui(config, d, None)
        d.gui = gui
        d.start()
        def later() -> None:
            gui.main()
        call_later(0.030,later)
    else:
        raise Exception("Could not start daemon, fd was None! FIXME!")

    return "Bitcoin Cash FTW!"
