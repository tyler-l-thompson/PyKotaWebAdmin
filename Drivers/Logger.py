'''
Created on Aug 12, 2016

@author: Tyler Thompson
'''

import datetime, os

class Logger(object):
    '''
    classdocs
    '''


    def __init__(self, logFile, who=""):
        '''
        logfile - path to log file used by entire program.
        '''
        self.logfile = logFile
        self.touchLog()
        self.who = who
        
    '''
    Description: Log a message to the log file.
    Usage: Logger.Logger().log('Message to log')
    Parameters: message - The nessage to send to the log.
    Returns: None
    '''
    def log(self, message):
        logMonth = self.getLogMonth()
        logYear = self.getLogYear()
        if self.checkLogMonth(logMonth) == False:
            self.moveLog(logMonth, logYear)
        path = self.checkLogYear(logMonth, logYear)
        if path != None:
            os.remove(path)
        timestamp = str(datetime.datetime.now())
        logfile = open(self.logfile, 'a')
        logfile.write('\n' + timestamp + ": " + self.who + ": " + message)
        logfile.close()
        
    '''
    Description: Touches the log file.
    Usage: self.touchLog()
    Parameters: None
    Returns: None
    '''
    def touchLog(self):
        if not os.path.isfile(self.logfile):
            log = open(self.logfile, 'a')
            timestamp = str(datetime.datetime.now())
            log.write(timestamp)
            log.close()
        try:
            os.chmod(self.logfile, 0777)
        except:
            None
        
    '''
    Description: Compares the current month to the month of the log.
    Usage: self.checkLogMonth(logMonth)
    Parameters: logMonth - The month of the current log.
    Returns: False - Log is at least 1 month old. | True - Log is less than 1 month old.
    '''
    def checkLogMonth(self, logMonth):
        curMonth = int(datetime.date.today().month)
        if curMonth != logMonth:
            return False
        else:
            return True
    
    '''
    Description: Uses the current log month and year to find and remove a log that is at least 1 year old.
    Usage: self.checkLogYear(logMonth, LogYear)
    Parameters: logMonth - The month of the current log. | logYear - the year of the current log.
    Returns: path - The path of the out of date log if there is one. | None - No out of date logs found.
    '''
    def checkLogYear(self, logMonth, logYear):
        path = str(self.logfile + "." + str('%02d' % logMonth) + str(logYear - 1))
        isPath = os.path.exists(path)
        if isPath == True:
            return path
        else:
            return None
        
    '''
    Description: Gets the month of the current log file.
    Usage: self.getLogMonth()
    Parameters: None
    Returns: The log month as an integer.
    '''
    def getLogMonth(self):
        log = open(self.logfile, 'r')
        lines = log.readlines()
        log.close()
        try:
            logMonth = int(lines[len(lines) - 1][5:7])
        except:
            logMonth = int(datetime.date.today().month)
        return logMonth
        
    '''
    Description: Get the year of the current log file.
    Usage: self.getLogYear()
    Parameters: None
    Returns: The log year as an integer.
    '''
    def getLogYear(self):
        log = open(self.logfile, 'r')
        lines = log.readlines()
        log.close()
        return int(lines[len(lines) - 1][0:4])
        
    '''
    Description: Archives the current log with its log date as an extension.
    Usage: self.moveLog(logMonth, logYear)
    Parameters: logMonth - The month of the log to move. | logYear - The year of the log to move.
    Returns: None
    '''
    def moveLog(self, logMonth, logYear):
        month = str('%02d' % logMonth)
        year = str(logYear)
        newfile = self.logfile + '.' + month + year
        os.rename(self.logfile, newfile)
        self.touchLog()