import atexit
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import json
from datetime import datetime

from os import path

#while True:
#    try:
#        config = input("Please enter config file: \n ")
    #Input is "python <script name> <config file name>.config
#        if path.isfile(config) == True:
#            break
#            
#        else:
#            print("Ooops!!! That config file isn't in the current dir. \n ")
#    except ValueError:
#        print("Enter valid config file:\n")
#        continue

ZNY_DIST_PATH = '/home/users/gbg/hanksea/ATChecklist/ZNY/DIST/'
ZOA_DIST_PATH = '/home/users/gbg/hanksea/ATChecklist/ZOA/DIST/'

load_proc = ''
fdps = ''
post_cmd = ''
#test_run = 0
load_cmd = ''



def post_files():
    #Check which Auto test;  2 = ZOA_DIL, 3 = ZNY_DIL, ATC_ZOA = 4, ATC_ZNY = 5
    if test_run == 2:
        post_cmd = './zoadil_post_T28 ' + config
    elif test_run == 3:
        post_cmd = './t31_POST ' + config
    elif test_run == 4:
        post_cmd = './zoa_atchecklist_post_T28 ' + config
    elif test_run == 5:
        post_cmd = './zny_atchecklist_post_T28 ' + config
    

    print("Posting files........")
    p = subprocess.Popen(post_cmd, shell=True, stdout=subprocess.PIPE)
    print( p.communicate())
    p.wait()
    pRc = p.returncode
    if pRc == 0:
    #returncode = 0 means successfull subprocess completion
        print("Post successfull...... \n")
    else:
        print("Post was UNsuccessfull..... \n \n \n")
        
    

def check_load_file(lp):
    print("checking if load file exists for single box.......")
    
    COMMAND1 = "cd /ocean21/bootstrap\n"
    COMMAND2 = "./check_load_file " + lp
    HOST = "atop@" + lp
    print("Command2: " + COMMAND2)
    ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND1, COMMAND2],
                   shell=False,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print (sys.stderr, "ERROR: %s" % error)
    else:
        tmp = result[0].strip()
        print (str(tmp))
        return str(tmp)

def find_load_proc():
    #find the right processor in the config file to load from, then load the lab/box
    load_proc = ""
    fdps= "" 
    with open(config) as f:
        lines = f.read().splitlines()
        #print("lines: ", lines) #prints the whole array, aka the whole file: ['cwpa101', 'cwpa102', 'cwpa103', 'cwpa104',] etc
        for i in lines:
            print("For loop: " + i)    
            #if statement finds the fdps nad mcpp in the config file if there is one and assigns the mcpp string to the 'load_proc' variable and the fdps to the 'fdps' variable
            if len(lines) == 1:
                load_proc = i
                break
            elif load_proc != "" and fdps != "":
                break
            elif load_proc == "" and i.startswith('mcp') and i.endswith('1'):
                load_proc = i.strip()    
            elif load_proc == "" and i.startswith('mcp') and i.endswith('2'):
                load_proc = i.strip()     
            elif fdps == "" and "fdps" in i:
                fdps = i 

    if load_proc == "" or fdps == "":
        print ("Cannot find MCP or FDP in config file.")
        print ("mcp: ", load_proc)
        print ("fdps: ", fdps)
        exit()
    
    #error handling for single processor
    if load_proc == "" and len(lines) == 1:
        print ("Cannot find cwp and in config file.")
        exit()

    print ("finished find_load_proc() load_proc var is " +load_proc)
    
    if len(lines) > 1:
        print ("finished find_load_proc() fdps var is  " + fdps)

    print("end of find_load_proc")
    return load_proc, fdps


def load_lab():
    #For half and full lab configs
    if 'mcp' in load_proc:
        #print ("This is not a single proc test")
        RELCMD = "echo $(cd /ocean21/bootstrap;pwd -P) | egrep -o '.{1,22}$'"
        FDPHOST = "atop@"+fdps
        MCPHOST = "atop@"+load_proc
        #need to know the release. one way is by checking the mcp ocean21 directory.
        sshOpen = subprocess.Popen(["ssh", "%s" % FDPHOST , RELCMD ],
                   shell=False,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
        release = sshOpen.stdout.readlines()
        release = release[0].decode().replace("\n", "")
        if release == []:
            error = sshOpen.stderr.readlines()
            print (sys.stderr, "ERROR: %s" % error)
            print ("Could not find the release. Please enter the release you are running.")
            return False
        else:
            print ("")
            #return True
            print ("Starting lab on "+ load_proc)
            loadconfig = config.replace(".config", "")
            LOADCMD = "load -conf {} -platform {} -env test -validate off -noconfirm -dae -recov 3" .format(release, loadconfig)
            print (LOADCMD)
            sshLoad = subprocess.Popen(["ssh", "%s" % MCPHOST , LOADCMD ],
                   shell=False,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
            sshLoad.wait() 
            print ("Please check the MCP to see if it loaded. Hint: If running on sbalc01, please make sure startvnc is turned on")
            print ("")
            return True

    
    #This is used for single proc.     
    if 'mcp' not in load_proc:
        var = str(check_load_file(load_proc))[2:5]
        print("Var: " + var)
    #exit()
        if var == 'No':
            print("Cannot load_single. Please create a " + "load_" +load_proc + "_cfg.com file and add it to the /ocean21/bootstrap directory and try running script again.")
            sys.exit()
        elif var == 'Yes': 
        
            load_cmd = 'load_single ' + load_proc    
            #print("Load lab from:  " + load_proc)
            print("Load command: " + load_cmd)
    
            print("Loading lab.....")    
            p2 = subprocess.Popen(load_cmd, shell=True, stdout=subprocess.PIPE)
            p2.wait()
            if p2.returncode == 0:
                print("Initial Load command was successfull waiting for lab to come up....")
                time.sleep(300)
            print(p2.returncode)    


def auto_run_py(tr, proc):
    #modular python run script def.  This logs onto the box the lab was loaded from (mcpp or a single box) and kicks off the scenario py script based on the 'test_run' value. 
     
    print("auto_run: " + load_proc)
    #time.sleep(150)
    COMMAND1 = "cd /ocean21/bootstrap\n"
    COMMAND2 = "python3 ZNY_ATCKLST_M.py " +str(tr)  +"\n"
    
    HOST = "atop@"+proc
    print("Loading from........ " +HOST)
    print("COMMAND2: " + COMMAND2)
    ssh = subprocess.Popen(["ssh", "%s" % HOST , COMMAND1, COMMAND2 ],
                   shell=False,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print (sys.stderr, "ERROR: %s" % error)
        return False
    else:
        print (result)
        return True
    


def unload_lab():
    COMMAND1 = "cd /ocean21/bootstrap\n"
    COMMAND2 = "unload -force -dae"
    HOST = "atop@" + load_proc
    ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND1, COMMAND2],
                   shell=False,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()
    if result == []:
        error = ssh.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        print (result)
        
           
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#END DEFINITIONS


#Ask user for input for config file name
while True:
    try:
        #Suggestion: list all the configs that are found within the current directory instead of manually typing in config.
        config = input("Please enter config file: \n ")
#Input is "python <script name> <config file name>.config
        if path.isfile(config) == True:
            break

        else:
            print("Ooops!!! That config file isn't in the current dir. \n ")
    except ValueError:
        print("Enter valid config file:\n")
        continue


#User Input to set test_run number
while True:
    try:
        test_run = int(input("What test are you running today? \n 1) ZAN Clean run \n 2) ZOA DIL \n 3) ZNY DIL \n 4) ZOA AT Checklist \n 5) ZNY AT Checklist\n"))
    except ValueError:
        print("Please enter a number between 1-5")
    else:
        break

load_proc,fdps = find_load_proc()
#print(load_proc + " : " + fdps)
print("\n")
#Run appropriate test commands for the user input values 1-5
print("here")
# Suggestion: instead of defining "test" in each elif, map it before (i think they're called python dictories). 
# Don't need to do elif each time since they will be running the same commands.
if test_run == 1:
    test = "ZAN Clean Run"
    print(test)
elif test_run == 2:
    test = "ZOA DIL"
    print(test)
    post_files()
    load_lab()
    time.sleep(300)

    print("Kicking off " + test + "...............\n")
    #print("starting FDP dp_comp.exe commands @ XX:XX ...")
    print(time.strftime("%H:%M:%S", time.localtime()))
    auto_run_py(test_run, fdps)
    unload_lab()    

elif test_run == 3:
    test= "ZNY DIL"
    print(test)
    post_files()
    load_lab()
    time.sleep(300)
    print("Kicking off " + test + "...............\n")    
 
    #print("starting FDP dp_comp.exe commands @ time: XX:XX ...")
    print(time.strftime("%H:%M:%S", time.localtime()))
    auto_run_py(test_run, fdps)
    unload_lab()

elif test_run == 4:
    test= "ZOA ATC"
    post_files()
    time.sleep(2)
    load_lab()
    time.sleep(300)

    print("Kicking off " + test + "...............\n")

    #Run ZOA ATC test run # and kick of test from FDPS
    print(time.strftime("%H:%M:%S", time.localtime()))
    auto_run_py(test_run, fdps)
    print("Auto run py finished!!!! Unloading lab.......\n")    
    unload_lab()

elif test_run == 5:
    test = "ZNY ATC"
    post_files()
    time.sleep(2)
    load_lab()
    time.sleep(300)

    print("Kicking off " + test + "...............\n")
    #Run loop on ZNY ATC Dictionary
    print(time.strftime("%H:%M:%S", time.localtime()))
    auto_run_py(test_run, load_proc)
    print("Auto run py finished!!!! Unloading lab.......\n")
    unload_lab()
    #print(test)
else:
    print("Invalid input " + str(test_run))

    
#print( "HEREERERERE, load_proc is: " + load_proc)

