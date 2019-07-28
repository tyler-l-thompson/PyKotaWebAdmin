'''
Created on Mar 14, 2017

@author: Tyler Thompson
'''

from pykota.tool import PyKotaTool
from pykota.storage import StorageUser
from pykota.storage import StorageGroup
from pykota.storage import StoragePrinter
from pykota.storage import StorageGroupPQuota
from pykota.storage import StorageUserPQuota
from pykota import version
import WMUldap, Logger, Config

class Pykota(PyKotaTool):
    '''
    classdocs
    '''
    def objectSetup(self, who=""):
        self.ldap = WMUldap.WMULdap()
        self.config = Config.Config()
        self.log = Logger.Logger(self.config.getConfig("logFile"), who)
        
    def version(self):
        return version.__version__
    
    def doc(self):
        return version.__doc__
        
    def getAllUsers(self):
        usernames = self.storage.getAllUsersNames()
        users = []
        for username in usernames:
            users.append(self.storage.getUser(username))
        return users

    def getAllGroups(self):
        groupnames = self.storage.getAllGroupsNames()
        groups = []
        for group in groupnames:
            groups.append(self.storage.getGroup(group))
        return groups

    def getAllPrinters(self):
        printernames = self.storage.getAllPrintersNames()
        printers = []
        for printer in printernames:
            printers.append(self.storage.getPrinter(printer))
        return printers

    def getNumberOfUsers(self):
        return len(self.storage.getAllUsersNames())
    
    def getNumberOfGroups(self):
        return len(self.storage.getAllGroupsNames())

    def getNumberOfPrinters(self):
        return len(self.storage.getAllPrintersNames())
    
    def getNumberOfUsersInGroup(self, groupId):
        return len(self.storage.getGroupMembers(self.storage.getGroup(groupId)))
    
    def addUsersByClassCRN(self, classCRN, accountBalance, overCharge, limitBy, groupId, wmuTerm, quotaSetup=True):
        # connect to ldap server
        ldapConnection = self.ldap.ldapConnect()
        if not ldapConnection:
            return "Failed to connect to ldap server. Please try again."

        # check if the class exists
        class_title = self.ldap.checkClassCRN(ldapConnection=ldapConnection,
                                            classCRN=classCRN,
                                            wmuTerm=wmuTerm)
        if not class_title:
            return "A class with CRN " + classCRN + " does not exist for term " + wmuTerm

        # get a list of students
        students = self.ldap.getPeopleInClass(ldapConnection=ldapConnection,
                                              classCRN=classCRN,
                                              wmuTerm=wmuTerm)
        if type(students) is not list:
            return "No students found to be enrolled in " + class_title + " for term " + wmuTerm + ". Please try again."

        # create group for new class
        curGroups = self.storage.getAllGroupsNames()
        if groupId != "" and groupId not in curGroups:
            self.addNewGroup(groupId, "CRN" + str(classCRN) + " Added by Class CRN Lookup", limitBy)

        # add the new users
        currentUsers = self.storage.getAllUsersNames() 
        for student in students:
            if student not in currentUsers:
                name = student[0]
                email = student[1]
                fullName = student[2]
                self.addNewUser(name, email, (classCRN + " - " + fullName), accountBalance, overCharge, limitBy, quotaSetup)
                if groupId != "":
                    self.addUserToGroup(name, groupId)
        return True
                
    def deleteUsersByClassCRN(self, classCRN):
        deletedUsers = []
        students = self.ldap.getPeopleInClass(classCRN)
        if students == False:
            return False
        currentUsers = self.storage.getAllUsersNames()
        for student in students:
            if student[0] in currentUsers:
                delUser = self.storage.getUser(student[0])
                self.log.log("DELETED USER: " + str(delUser.Name) + " " + str(delUser.Email) + " " + str(delUser.Description))
                deletedUsers.append(delUser.Name)
                delUser.delete()
        return deletedUsers
                
    def addNewUser(self, username, email, description, accountBalance, overCharge, limitBy, quotaSetup=True):
        currentUsers = self.storage.getAllUsersNames()
        if username in currentUsers:
            return False
        else:
            newUser = StorageUser(self.storage, username)
            newUser.setEmail(email)
            newUser.setDescription(description)
            newUser.setAccountBalance(accountBalance, accountBalance)
            newUser.setOverChargeFactor(overCharge)
            newUser.setLimitBy(limitBy)
            self.storage.addUser(newUser)
            self.log.log("ADDED USER: " + str(newUser.Name) + " " + str(newUser.Email) + " " + str(newUser.Description))

            '''Add new user to allusers group'''
            if "allusers" not in self.storage.getAllGroupsNames():
                self.addNewGroup("allusers", "All Users", "balance")
            self.addUserToGroup(newUser.Name, "allusers")

            '''Setup user quota on all printers unless specified'''
            if quotaSetup:
                printers = self.getAllPrinters()
                for printer in printers:
                    self.addUserPrinterQuota(printerId=printer.Name, userId=username)

            return True
        
        
    def addNewGroup(self, groupId, description, limitBy):
        currentGroups = self.storage.getAllGroupsNames()
        if groupId in currentGroups:
            return False
        else:
            newGroup = StorageGroup(self.storage, groupId)
            newGroup.setDescription(description)
            newGroup.setLimitBy(limitBy)
            self.storage.addGroup(newGroup)
            self.log.log("ADDED GROUP: " + str(newGroup.Name) + " " + str(newGroup.Description))
            return True
        
    def getUserGroup(self, userName):
        user = self.storage.getUser(userName)
        return self.storage.getUserGroups(user)
    
    def addUserToGroup(self, userName, groupId):
        user = self.storage.getUser(userName)
        group = self.storage.getGroup(groupId)
        self.storage.addUserToGroup(user, group)
        self.log.log("ADDED USER TO GROUP: " + str(group.Name) + " : " + str(user.Name))
    
    def deleteUserFromGroup(self, groupId, userId):
        self.storage.getGroup(groupId).delUserFromGroup(self.storage.getUser(userId))
        self.log.log("DELETED USER FROM GROUP: " + groupId + " : " + userId)
        
    def deleteAllUsersFromGroup(self, groupId):
        group = self.storage.getGroup(groupId)
        for user in self.storage.getGroupMembers(group):
            user.delete()
        self.log.log("DELETED ALL USERS FROM GROUP: " + groupId)
        
    
    def getAllGroupMembers(self, groups):
        allGroupMembers = []
        for group in groups:
            groupMembers = self.storage.getGroupMembers(group)
            groupInfo = []
            for member in groupMembers:
                groupInfo.append(member)
            allGroupMembers.append(groupInfo)
        return allGroupMembers
        
        
    def getUserPrinterQuota(self, printerId, userId):
        return self.storage.getUserPQuota(self.storage.getUser(userId), self.storage.getPrinter(printerId))

    def deleteUserPrinterQuota(self, printerId, userId):
        self.storage.getUserPQuota(self.storage.getUser(userId), self.storage.getPrinter(printerId)).delete()
        self.log.log("DELETED USER PRINT QUOTA: " + printerId + " : " + userId)

    def addUserPrinterQuota(self, printerId, userId):
        self.storage.addUserPQuota(StorageUserPQuota(self.storage, self.storage.getUser(userId), self.storage.getPrinter(printerId)))
        self.log.log("ADDED USER PRINT QUOTA: " + printerId + " : " + userId)
    
    def addPrinter(self, printerId, pricePerPage, pricePerJob, maxJobSize, passthroughMode):
        curPrinters = self.storage.getAllPrintersNames()
        if printerId in curPrinters:
            return False
        else:
            newPrinter = StoragePrinter(self.storage, printerId)
            newPrinter.setPrices(pricePerPage, pricePerJob)
            newPrinter.setMaxJobSize(maxJobSize)
            newPrinter.setPassThrough(passthroughMode)
            self.storage.addPrinter(newPrinter)
            self.log.log("ADDED PRINTER: " + printerId)
            return True
    
    def addGroupPrinterQuota(self, printerId, groupId):
        self.storage.addGroupPQuota(StorageGroupPQuota(self.storage, self.storage.getGroup(groupId), self.storage.getPrinter(printerId)))
        self.log.log("ADDED GROUP PRINT QUOTA: " + printerId + " : " + groupId)

    def deleteGroupPrinterQuota(self, printerId, groupId):
        self.storage.getGroupPQuota(self.storage.getGroup(groupId), self.storage.getPrinter(printerId)).delete()
        self.log.log("DELETED GROUP PRINT QUOTA: " + printerId + " : " + groupId)

    def getGroupPrinterQuota(self, printerId, groupId):
        return self.storage.getGroupPQuota(self.storage.getGroup(groupId), self.storage.getPrinter(printerId))

    def getAllGroupPrinterQuotas(self):
        printers = self.getAllPrinters()
        groups = self.getAllGroups()
        groupPrintQuotas = []
        for printer in printers:
            for group in groups:
                printQuota = self.getGroupPrinterQuota(printer.Name, group.Name)
                if printQuota.Exists == True:
                    groupPrintQuotas.append(printQuota)
        return groupPrintQuotas

    def getAllUserPrinterQuotas(self):
        printers = self.getAllPrinters()
        users = self.getAllUsers()
        userPrintQuotas = []
        for printer in printers:
            for user in users:
                printQuota = self.getUserPrinterQuota(printer.Name, user.Name)
                if printQuota.Exists == True:
                    userPrintQuotas.append(printQuota)
        return userPrintQuotas

    def getAllPrinterQuotaMembers(self, printerId):
        groups = self.getAllGroups()
        users = self.getAllUsers()
        printerQuotaMembers = []
        for group in groups:
            printQuota = self.getGroupPrinterQuota(printerId, group.Name)
            if printQuota.Exists == True:
                printerQuotaMembers.append(printQuota)
        for user in users:
            printQuota = self.getUserPrinterQuota(printerId, user.Name)
            if printQuota.Exists == True:
                printerQuotaMembers.append(printQuota)
        return printerQuotaMembers

    def getAllPrinterQuotaGroupMembers(self, printerId):
        groups = self.getAllGroups()
        printerQuotaMembers = []
        for group in groups:
            printQuota = self.getGroupPrinterQuota(printerId, group.Name)
            if printQuota.Exists == True:
                printerQuotaMembers.append(printQuota)
        return printerQuotaMembers

    def getAllPrinterQuotaUserMembers(self, printerId):
        users = self.getAllUsers()
        printerQuotaMembers = []
        for user in users:
            printQuota = self.getUserPrinterQuota(printerId, user.Name)
            if printQuota.Exists == True:
                printerQuotaMembers.append(printQuota)
        return printerQuotaMembers

    def getAllQuotas(self):
        printers = self.getAllPrinters()
        quotas = []
        for printer in printers:
            printerQuotaMembers = self.getAllPrinterQuotaMembers(printer.Name)
            for member in printerQuotaMembers:
                quotas.append(member)
        return quotas