'''
Created on Mar 5, 2017

@author: Tyler Thompson
'''

import json, os, Logger

class Config(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.configRoot = self.getConfigRoot()
        self.configPath = self.configRoot + "/webadmin.conf"
        self.log = Logger.Logger(self.getConfig("logFile"))
        
    '''
    Description: Get the value associated with the key passed from the config file.
    Usage: ConfigDriver.ConfigDriver().getConfig(key)
    Parameters: key - The key to look for the value of in the config.
    Returns: The value associated with the key in the config.
    '''
    def getConfig(self, key):
        try:
            with open(self.configPath) as configFile:
                data = json.load(configFile)
            return data[key]
        except:
            returnVal = key + " not found in config!"
            self.log.log("ERROR: " + returnVal + " Config Path: " + self.configPath)
            return returnVal

    def setConfig(self, key, value):
        settings = self.getAllSettings()
        settings[key] = value
        self.setAllSettings(settings)

    def getAllSettings(self):
        try:
            with open(self.configPath) as configFile:
                data = json.load(configFile)
            return data
        except:
            returnVal = "Error reading config!"
            self.log.log("ERROR: " + returnVal + " Config Path: " + self.configPath)
            return returnVal

    def setAllSettings(self, settings):
        try:
            with open(self.configPath, 'w') as configFile:
                configFile.write(json.dumps(settings, indent=4, sort_keys=True, ensure_ascii=False))
            return True
        except:
            returnVal = "Error saving config!"
            self.log.log("ERROR: " + returnVal + " Config Path: " + self.configPath)
            return False

    '''
    Description: Resolves the full path for the config files based on how this file is relatively called.
    Usage: self.getConfigRoot()
    Parameters: None
    Returns: The full path to the config directory as a string.
    '''    
    def getConfigRoot(self):
        root = os.path.abspath(__file__).split('/')
        try:
            root.remove(str(os.path.basename(__file__)))
            root.remove("Drivers")
        except:
            pass
        configRoot = ""
        for r in root:
            configRoot = configRoot + r + "/"
        return configRoot + "configs"