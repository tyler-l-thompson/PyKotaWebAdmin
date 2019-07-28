#!/usr/bin/python
'''
Created on April 10, 2017

@author: Tyler Thompson
'''

import sys, os

def getConfigRoot():
    root = os.path.abspath(__file__).split('/')
    try:
        root.remove(str(os.path.basename(__file__)))
        root.remove("tools")
    except:
        pass
    configRoot = ""
    for r in root:
        configRoot = configRoot + r + "/"
    return configRoot

sys.path.append(getConfigRoot())
from Drivers import Pykota

def main():
    username = sys.argv[1]
    clientip = sys.argv[2]
    printerid = sys.argv[3]
    os.system("echo " + str(username + " " + clientip + " " + printerid) + " > /opt/testing.txt")
    pyKotaMan = Pykota.Pykota()
    pyKotaMan.deferredInit()
    user = pyKotaMan.storage.getUser(username)
    if user.Exists == False:
        print "User does not exists"
        os.system("/usr/local/bin/pknotify --destination " + clientip + ":7654 --timeout 60 --notify 'You are currently not setup to print from printer " + printerid + ". Please see an administrator for help.'")
    else:
        print user.Name, user.Description, user.AccountBalance



if __name__ == '__main__':
    main()
