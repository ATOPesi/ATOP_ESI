import atexit
import logging
import os
import socket
import subprocess
import sys
import threading
import time

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
    #Check which Auto test
    if test_run == 5:
        post_cmd = './zny_atchecklist_post_T28 ' + config
    elif test_run == 4:
        post_cmd = './zoa_atchecklist_post_T28 ' + config
    
    print("Posting files........")
    p = subprocess.Popen(post_cmd, shell=True, stdout=subprocess.PIPE)
    #print( p.communicate())
    p.wait()
    print(p.returncode)

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
    load_proc = ''
    fdps= '' 
    with open(config) as f:
        lines = f.read().splitlines()
        #print(lines)
        for i in lines:
            #if statement finds the fdps nad mcpp in the config file if there is one and assigns the mcpp string to the 'load_proc' variable and the fdps to the 'fdps' variable
            if "mcppa101" in lines or "mcppb601" in lines or "mcppa102" in lines or "mcppb602" in lines:
                if i == "mcppa101":
                    load_proc = i
                    
                elif i == "mcppb102":
                    load_proc = i
                 
                elif i == "mcppa102":
                    load_proc = i
                    
                elif i == "mcppb602":
                    load_proc = i
                    
            elif "fdpsa101" in lines or "fdpsa102" in lines or "fdpsb601" in lines or "fdpsb602" in lines:
                if i == "fdpsa101" or "fdpsa102" or "fdpsb601" or "fdpsb602":
                    fdps = i
            
            elif len(lines) == 1:
                load_proc = i
                break
            else:
                lines.remove(i)
    print ("finished find_load_proc(): " +load_proc)
    print ("finished find_load_proc() fdps var is  " + fdps)
    return load_proc, fdps


def load_lab():
        
    print("Load_proc: " + load_proc)
    var = str(check_load_file(load_proc))[2:5]
    print("Var: " + var)
    if var == 'No':
        print("Cannot load_single. Please create a " + "load_" +load_proc + "_cfg.com file and add it to the /ocean21/bootstrap directory and try running script again.")
        sys.exit()
    elif var == 'Yes': 
        load_cmd = 'load.sh ' + load_proc    
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
    #COMMAND3 = str(tr) + "\n"
    HOST = "atop@"+proc
    print("Loading from........ " +HOST)
    #print("COMMAND3: " + COMMAND3)
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

#Run appropriate test commands for the user input values 1-5
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
    post_files()
    time.sleep(2)
    load_lab()
    #time.sleep(300)

    print("Kicking off " + test + "...............\n")

    #Run ZOA ATC test run # and kick of test from FDPS
    auto_run_py(test_run, fdps)


     #   print(test)
elif test_run == 5:
    test = "ZNY ATC"
    post_files()
    time.sleep(2)
    load_lab()
    time.sleep(300)

    print("Kicking off " + test + "...............\n")
    #Run loop on ZNY ATC Dictionary
    auto_run_py(test_run, load_proc)
    print("Auto run py finished!!!! Unloading lab.......\n")
    unload_lab()
    #print(test)
else:
    print("Invalid input " + str(test_run))

    
#print( "HEREERERERE, load_proc is: " + load_proc)

