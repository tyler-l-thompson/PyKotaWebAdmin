'''
Created on Sep 2, 2016

@author: Tyler Thompson
'''
import ldap, Config, Logger

class Ldap(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.config = Config.Config()
        self.log = Logger.Logger(self.config.getConfig('logFile'))
        self.serveraddress = self.config.getConfig("loginLdapServerAddress")
        self.adminusername = self.config.getConfig("loginLdapAdminDN")
        self.adminpassword = self.config.getConfig("loginLdapAdminPass")
        self.basedn = self.config.getConfig("loginLdapBaseDN")
        self.admindn = self.config.getConfig("loginLdapAdminDN")
        self.userdn = None
        #ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        
    def login(self, username, password):
        if self.initialize() == False:
            return ['0',"Failed to connect to ldap server."]
        if self.setUserDn(username) == False:
            return ['0',"Username not found."]
        if self.authenticate(username, password) == False:
            return ['0',"Username or password incorrect."]
        if self.getValidUsers(username) == True:
            return ['1', 'PyKota Administrators']
        group = self.getGroup(username)
        if group == False:
            return ['0', 'You do not have rights to access this page.']
        return ['1', group]
        
        
    def initialize(self):
        try:
            ldapConnection = ldap.initialize(self.serveraddress)
            ldapConnection.simple_bind_s(self.admindn, self.adminpassword)
            ldapConnection.unbind_s()
            return True
        except:
            return False
        
    def setUserDn(self, uid):
        try:
            ldapConnection = ldap.initialize(self.serveraddress)
            ldapConnection.simple_bind_s(self.admindn, self.adminpassword)
            ldapSearch = ldapConnection.search("cn=users," + self.basedn, ldap.SCOPE_SUBTREE, 'uid='+uid)
            results = []
            while 1:
                resultType, resultData = ldapConnection.result(ldapSearch, 0)
                if resultData == []:
                    break
                else:
                    if resultType == ldap.RES_SEARCH_ENTRY:
                        results.append(resultData)
            searchDn = results[0][0][0] 
            self.userdn = searchDn
            ldapConnection.unbind_s()
            return True
        except:
            return False
        
        
    def authenticate(self, username, password):
        ldapConnection = ldap.initialize(self.serveraddress)
        try:
            ldapConnection.simple_bind_s(self.userdn, password)
            ldapConnection.unbind_s()
            return True
        except ldap.INVALID_CREDENTIALS:
            ldapConnection.unbind_s()
            return False

    def getValidUsers(self, username):
        validusers = self.config.getConfig('loginLdapUsers').strip().split(',')
        if username in validusers:
            return True
        else:
            return False

    def getGroup(self, username):
        validGroups = self.config.getConfig('loginLdapGroups').strip().split(',')
        for validGroup in validGroups:
            valid = False
            members = self.getGroupMembers(validGroup)
            for i in range(len(members)):
                if username == members[i]:
                    valid = True
            if valid == True:
                return validGroup
        return False

        # admin = False
        # admins = self.getGroupMembers("administrators")
        # for i in range(len(admins)):
        #     if username == admins[i]:
        #         admin = True
        # if admin == True:
        #     return 'administrators'
        #
        # attendant = False
        # attendants = self.getGroupMembers("attendants")
        # for i in range(len(attendants)):
        #     if username == attendants[i]:
        #         attendant = True
        # if attendant == True:
        #     return 'attendants'
        #
        # director = False
        # directors = self.getGroupMembers("directors")
        # for i in range(len(directors)):
        #     if username == directors[i]:
        #         director = True
        # if director == True:
        #     return 'directors'
        # return False
        
       
    def getGroupMembers(self, group):
        ldapConnection = ldap.initialize(self.serveraddress)
        ldapConnection.simple_bind_s(self.admindn, self.adminpassword)
        try:
            ldapSearch = ldapConnection.search(self.basedn, ldap.SCOPE_SUBTREE, 'cn=' + group)
            results = []
            while 1:
                resultType, resultData = ldapConnection.result(ldapSearch, 0)
                if resultData == []:
                    break
                else:
                    if resultType == ldap.RES_SEARCH_ENTRY:
                        results.append(resultData) 
            members = results[0][0][1]['memberUid']
        except:
            ldapConnection.unbind_s()
        return members
       
    def getName(self, uid):
        ldapConnection = ldap.initialize(self.serveraddress)
        ldapConnection.simple_bind_s(self.admindn, self.adminpassword)
        try:
            ldapSearch = ldapConnection.search(self.basedn, ldap.SCOPE_SUBTREE, 'uid=' + uid)
            results = []
            while 1:
                resultType, resultData = ldapConnection.result(ldapSearch, 0)
                if resultData == []:
                    break
                else:
                    if resultType == ldap.RES_SEARCH_ENTRY:
                        results.append(resultData) 
            name = results[0][0][1]['cn'][0]
        except:
            ldapConnection.unbind_s()
            name = 'n/a'
        return name