#!/usr/bin/env python

#Developed for automating ESI AUTO tests ZOA/ZNY DIL and ZOA/ZNY/ZAN AT Checklist tests
#Version 1.0 of Script - 11/30/21

import atexit
import logging
import os
import socket
import subprocess
import sys
import threading
import time

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger()
procs = []
test = None


#def ecs_command:
#inputs - command line string or array of characters
#purpose - sets up all EITT windows via subprocesses and hardcoded arguments.  This could be improved to allow for different types of EITT setups depending on the test being executed. 


def ecs_command(cmd):
    p = None
    with open(cmd['log'], 'w') as log:
        p = subprocess.Popen(cmd['cmd'].split(' '), stdin=subprocess.PIPE, stdout=log, stderr=log)
    procs.append(p)
    time.sleep(cmd['input_wait'])
    for arg in cmd['inputs']:
        #poll() = returns None if process p is not finished yet
        if p.poll() is None:
            out = p.communicate(input=arg)[0]
            #p.stdin.write(b'\n')
            time.sleep(15)


def exit_handler():
    logger.info('\nStopping EITT. Please Wait...')
    os.system('killsim')
    for p in procs:
        if p.poll() is None:
            p.terminate()
    return

#env_setup() - Checks DSSC release path variable on SIM server?  ECSSIMS301? what server is this scrpit to be run on again???
def env_setup():
    if os.getenv('DSSC_REL_PATH') is None:
        logger.info('Please setup your release by running:\n\n\t. set_dssc -s ; . run_setup ; site_setup anc direct\n')
        sys.exit()


def main(args=None):
    #env_setup()
    atexit.register(exit_handler)

    pb_file = 'zanbkgd_withWeather.pb'
    #if os.getenv('DSSC_REL') and (int(os.getenv('DSSC_REL')[1:3]) > 28):
     #   pb_file = 'upleveled_' + pb_file

    # Set up the dictionaries
    ZAN_cmds = [
        {'cmd' : 'interface_connector.exe', 'inputs' : [], 'input_wait' : 0, 'log' : 'py_interface_connector.log'},
        {'cmd' : 'simipif.exe', 'inputs' : [], 'input_wait' : 0, 'log' : 'py_simipif_exe.log'},
        {'cmd' : 'runsim -nodisplay', 'inputs' : ['zanbkgd_wrkload_new.fp'], 'input_wait' : 5, 'log' : 'py_runsim.log'},
        {'cmd' : 'simipif.pl -norad_full zan', 'inputs' : [], 'input_wait' : 0, 'log' : 'py_simipif_pl.log'},
        {'cmd' : 'SimDlk.exe', 'inputs' : ['load zanbkgd_site12.dlk', 'run zanbkgd_site12.dlk'], 'input_wait' : 5, 'log' : 'py_simdlk.log'},
        {'cmd' : '/ocean21/bootstrap/mearts/runops_eitt.sh /home/atop/{0}'.format(pb_file), 'inputs' : [], 'input_wait' : 0, 'log' : 'py_runops_eitt.log'},
        {'cmd' : '/ocean21/bootstrap/mearts/wxsim 22223 -s /home/atop/warpPERF.scn', 'inputs' : [], 'input_wait' : 0, 'log' : 'py_wxsim.log'},
    ]

    ZNY_ATCL_cmds = [ 
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'sysdown\nY\nexit\n'], 'input_wait': 5, 'log' : 'py_dpcomp.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'fz\nsetsystime 0000\nsysstart\nexit\n'], 'input_wait': 70, 'log' : 'py_setup.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run NY.cmd\n'], 'input_wait': 3, 'log' : 'py_sysstart.log'}
        ]

    ZNY_ATCL_cmdsV2 = [
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'sysdown\nY\nsleep 10\nfz\nsetsystime 0000\nsysstart\nsleep 150\nrun NY.cmd\nsleep 120\nexit\n'], 'input_wait': 5, 'log' : 'py_ZNY_ATC.log'}
        ]



    ZOA_ATCL_cmds = [
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'sysdown\nY\nexit\n'], 'input_wait': 5, 'log' : 'py_dpcomp.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run at_zoa_aidc2_config\nsysstart\nexit\n'], 'input_wait': 50, 'log' : 'py_setup.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run OAK.cmd\n'], 'input_wait': 30, 'log' : 'py_OAK.log', 'test_time' : 0,}
        ]
    
    ZNY_DIL_cmds = [
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'sysdown\nY\nexit\n'], 'input_wait': 5, 'log': 'sysdown.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run znydil_config\nsysstart\nexit\n'], 'input_wait': 10, 'log': 'znydil.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run t31_signon.cmd\nexit\n'], 'input_wait': 100, 'log': 'signon.log'},
        {'cmd' : 'dp_comp.exe', 'inputs' : [b'run t31_znydil.cmd\n'], 'input_wait': 180, 'log': 'dil.log'}


	]
	
    ZOA_DIL_cmds = [
        {'cmd' : 'dp_comp.exe'}

        ]

    #Auto Test Times array
    
    run_time = 0

    test_run = int(sys.argv[1])
    print("Arg for test_run: "  + str(test_run))
    if test_run == 1:
        test = "ZAN Clean Run"
        print(test) 
    elif test_run == 2:
        test = "ZOA DIL"
        print(test)
    elif test_run == 3:
        test= "ZNY DIL"
        print(test)
    elif test_run == 4:
        test= "ZOA ATC"
        for c in  ZOA_ATCL_cmds:
            ecs_command(c) 
        
        print(test)
    elif test_run == 5:
        test = "ZNY ATC"
        run_time = 4 * 60
        for c in  ZNY_ATCL_cmdsV2:
            ecs_command(c)
        
    else:
        print("Invalid input " + str(test_run))


    # Each dp_comp set of commands (sysdown, setup/sysstart, run scenario)
#    for c in cmds:
 #       ecs_command(c)
        

    # Wait for ATCKLIST ZNY test time (5 mins)
    try:
        logger.info( test +' is Running')
        while 1:
            print("Run time: " + run_time)    
            time.sleep(run_time)
            sys.exit()
    except KeyboardInterrupt:
        sys.exit()

if __name__ == '__main__':
    main(sys.argv[1:])


