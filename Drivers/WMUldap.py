'''
Created on Mar 16, 2017

@author: Tyler Thompson
'''

import ldap, Config, Logger, time

class WMULdap(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.config = Config.Config()
        self.log = Logger.Logger(self.config.getConfig("logFile"))
        self.serveraddress = self.config.getConfig("userBackendLdapServerAddress")
        self.userbasedn = self.config.getConfig("userBackendLdapBaseDN")
        self.admindn = self.config.getConfig("userBackendLdapAdminDN")
        self.adminpassword = self.config.getConfig("userBackendLdapAdminPassword")
        #ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        
    def getCurrentTerm(self, ldapConnection):
        termNumber = self.ldapReadFeild(ldapConnection, "cn=current,ou=WMUcourses,o=wmich.edu,dc=wmich,dc=edu", 'wmuTermNumber')
        #take out that random zero on the end?
        #Apparently this isn't needed anymore???
        # if int(termNumber[len(termNumber) - 1]) == 0:
        #     termNumber = termNumber[:-1]
        self.log.log(message="getCurrentTerm - Term: " + str(termNumber))
        return termNumber

    def getCurrentTermName(self):
        ldapConnection = self.ldapConnect()
        if ldapConnection == False:
            return "Failed to lookup."
        name = self.ldapReadFeild(ldapConnection, "cn=current,ou=WMUcourses,o=wmich.edu,dc=wmich,dc=edu", 'wmuTerm')
        ldapConnection.unbind()
        self.log.log(message="getCurrentTermName - Name: " + str(name))
        return name

    def getAllTerms(self):
        ldapConnection = self.ldapConnect()
        if ldapConnection == False:
            return [["Failed to lookup.", "Failed to lookup."]]
        terms = self.ldapSearch(ldapConnection=ldapConnection,
                                dn="ou=WMUcourses,o=wmich.edu,dc=wmich,dc=edu",
                                searchFilter=('objectClass=wmichTerm'),
                                searchField0="uid",
                                searchField1="wmuTerm")
        ldapConnection.unbind()
        self.log.log(message="getAllTerms - Terms:" + str(terms))
        return terms

    def checkClassCRN(self, ldapConnection, classCRN, wmuTerm):
        """
        Check if a class exists.
        :param classCRN: CRN number
        :return: Title | False
        """
        class_lookup = self.ldapSearch(ldapConnection=ldapConnection,
                             dn="ou=" + wmuTerm + ",ou=WMUcourses,o=wmich.edu,dc=wmich,dc=edu",
                             searchFilter=("wmuCallNumber=" + classCRN),
                             searchField0="title")
        self.log.log(message="checkClassCRN - CRN:" + str(classCRN) + " Term:" + str(wmuTerm) + " Lookup:" + str(class_lookup))
        if not class_lookup:
            return False
        else:
            return class_lookup[0]

    def getPeopleInClass(self, ldapConnection, classCRN, wmuTerm):
        """
        Get a list of student uids that are enrolled in a class.
        :param classCRN: The CRN number of the class
        :param wmuTerm: The term number.
        :return: A list of uids | False
        """
        students = self.ldapSearch(ldapConnection=ldapConnection,
                                   dn=self.userbasedn,
                                   searchFilter=("wmuEnrolledCallNumber=" + wmuTerm + classCRN),
                                   searchField0="wmuUID",
                                   searchField1="mail",
                                   searchField2="displayName")
        self.log.log(message="getPeopleInClass - CRN:" + str(classCRN) + " Term:" + str(wmuTerm) + " Students:" + str(students))
        if not students:
            # account for wmu ldap to have misinformation. This should fix the missing or not missing zero at the end of the current term number.
            currentTerm = wmuTerm[:-1]
            students = self.ldapSearch(ldapConnection=ldapConnection,
                                       dn=self.userbasedn,
                                       searchFilter=("wmuEnrolledCallNumber=" + currentTerm + classCRN),
                                       searchField0="wmuUID",
                                       searchField1="mail",
                                       searchField2="displayName")
            self.log.log(message="Try 2, getPeopleInClass - CRN:" + str(classCRN) + " Term:" + str(currentTerm) + " Students:" + str(students))
            if not students:
                return False
        return students
         
    def ldapSearch(self, ldapConnection, dn, searchFilter, searchField0, searchField1=None, searchField2=None):
        # print "DEBUG: ldapSearch | dn: " + str(dn) +  " searchFilter: " + str(searchFilter) + " searchField0: " + str(searchField0) + " searchField1: " + str(searchField1) + " searchField2: " + str(searchField2)
        '''Attempt to search ldap server 5 times before failing'''
        for i in range(0, 5):

            '''Start the search'''
            try:
                result_set = "LDAPSEARCH Function failure!"
                trys = 1

                '''Loop until ldap search returns either 5 empty sets or good data'''
                while True:

                    ldap_result_id = ldapConnection.search(dn, ldap.SCOPE_SUBTREE, searchFilter)
                    #print "DEBUG: ldap_result_id: " + str(ldap_result_id)
                    #print ldap.SCOPE_SUBTREE
                    result_set = []

                    '''Loop until all object info has been read'''
                    while 1:

                        '''Try to read the ldap object data'''
                        try:
                            result_type, result_data = ldapConnection.result(ldap_result_id, 0)
                            #print "DEBUG: result_type result_data: " + str(result_type) + " " + str(result_data)
                            '''when there is no more information to read, break'''
                            if not result_data:
                                break
                            else:

                                '''filter the search data for specified fields'''
                                try:
                                    filtered_data = result_data[0][1][searchField0][0]
                                    if searchField1 != None and searchField2 == None:
                                        filtered_data1 = result_data[0][1][searchField1][0]
                                        filtered_data = [ filtered_data, filtered_data1 ]
                                    if searchField1 != None and searchField2 != None:
                                        filtered_data1 = result_data[0][1][searchField1][0]
                                        filtered_data2 = result_data[0][1][searchField2][0]
                                        filtered_data = [ filtered_data, filtered_data1 , filtered_data2 ]
                                    if result_type == ldap.RES_SEARCH_ENTRY:
                                        result_set.append(filtered_data)
                                except KeyError:
                                    # self.log.log("Failed to find key in object:" + str(e) + " " + str(result_data))
                                    # filtered_data = "Failed to find key in object"
                                    pass
                                # if result_type == ldap.RES_SEARCH_ENTRY:
                                #     result_set.append(filtered_data)
                        except ldap.LDAPError, e:
                            self.log.log(str(e))

                    #print result_set

                    '''Check how many times the search got not data'''
                    if result_set:
                        break
                    elif trys > 5:
                        self.log.log("LDAPSEARCH Failed to get any info from ldap server!")
                        break
                    else:
                        trys = trys + 1

                return result_set

            except ldap.LDAPError, e:
                self.log.log("LDAP SEARCH FAILURE: " + str(i) + " : " + str(e))
                print "LDAP SEARCH FAILURE: " + str(i)
                time.sleep(0.2)
        print "LDAP SEARCH FAILED"
        return "Failed to lookup value"
            
    
    def ldapReadFeild(self, ldapConnection, dn, field):
        returnField = False
        for i in range(0,5):
            try:
                ldap_result = ldapConnection.read_s(dn)
                returnField = ldap_result[field][0]
                return returnField
            except ldap.LDAPError, e:
                self.log.log("LDAP LOOKUP FAILURE: " + str(i) + " : " + str(e))
                time.sleep(0.2)
        return returnField
        
    def ldapConnect(self):
        try:
            ldapConnection = ldap.initialize(self.serveraddress)
            ldapConnection.set_option(ldap.OPT_TIMEOUT, 5)
            ldapConnection.simple_bind_s(self.admindn, self.adminpassword)
        except ldap.LDAPError, e:
            self.log.log("ldapConnect - " + str(e) + " " + self.serveraddress + " " + self.admindn)
            ldapConnection = False
        return ldapConnection
