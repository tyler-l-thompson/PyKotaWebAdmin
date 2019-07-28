'''
Created on Mar 13, 2017

@author: Tyler Thompson
'''
import os, ssl, commands, socket
from flask import Flask, render_template, request, session, redirect
from flask_menu import Menu, register_menu
from datetime import timedelta
from mx import DateTime
from Drivers import Logger, Ldap, Config, Pykota, Git

ld = Ldap.Ldap()
config = Config.Config()
log = Logger.Logger(config.getConfig("logFile"))

if config.getConfig("enableSSL") == "True":
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(config.configRoot + "/PyKotaWebAdmin.crt", config.configRoot + "/PyKotaWebAdmin.key")

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(minutes=60)
Menu(app=app)

pyKotaMan = None

@app.route("/")
@register_menu(app, '.', "Home")
def main():
    session.permanent = True
    
    if not session.get('sorton'):
        session['sorton'] = "Name"
        
    if config.getConfig("enableUserLogin") == "False":
        session['logged_in'] = True 
  
    if not session.get('logged_in'):
        return render_template('login.html')

    if session.get('clientip') != None:
        session['admininfo'] = (session.get('username') + "@" + session.get('clientip'))
    else:
        session['admininfo'] = ""

    global log
    log = Logger.Logger(config.getConfig("logFile"), session['admininfo'])

    global pyKotaMan
    pyKotaMan = Pykota.Pykota()
    pyKotaMan.deferredInit()
    pyKotaMan.objectSetup(session['admininfo'])

    users = pyKotaMan.getAllUsers()
    printers = pyKotaMan.getAllPrinters()
    groups = pyKotaMan.getAllGroups()

    session['version'] = pyKotaMan.version()
    session['doc'] = pyKotaMan.doc()
    session['lookupuser'] = None
    session['editgroup'] = None
    session['addgroup'] = None
    session['editprinterquota'] = None
    session['addprinterquota'] = None
    session['viewgroup'] = None
    session['crnlookup'] = False
    session['hostip'] = socket.gethostbyname(socket.gethostname())

    return render_template("mainpage.html", users=users, printers=printers, groups=groups, returnurl='/', summaryview="read")

@app.route("/users", methods=['POST', 'GET'])
@register_menu(app, '.users', 'Users', order=0)
def users():
    if not session.get('logged_in'):
        return redirect("/")
    users = pyKotaMan.getAllUsers()
    
    if "userid" in request.form:
        userId = request.form['userid']
        if userId == "*" or userId == "":
            lookupUsers = pyKotaMan.getAllUsers()
        else:
            lookupUsers = [ pyKotaMan.storage.getUser(userId) ]
            if lookupUsers[0].Email == None and lookupUsers[0].Description == None and lookupUsers[0].AccountBalance == None and lookupUsers[0].LifeTimePaid == None:
                return render_template('message.html', alertLevel="error", message="The following user doesn't exists: " + userId, returnurl="/edituser")
        return render_template('users/users.html', users=lookupUsers, returnurl="/users", summaryview="read")
    else:
        lookupUsers = pyKotaMan.getAllUsers()
        return render_template('users/users.html', users=lookupUsers, returnurl="/users", summaryview="read")
    
    #return render_template('users.html', users=users, summaryview='read', returnurl='/users')

@app.route("/adduser", methods=['GET', 'POST'])
@register_menu(app, '.users.adduser', 'Add User(s)', order=0)
def adduser():
    if not session.get('logged_in'):
        return redirect("/")

    if session.get('crnlookup') == True:
        session['crnlookup'] = False
        addStatus = pyKotaMan.addUsersByClassCRN(session.get('crnClass'), session.get('crnAccountBalance'), session.get('crnOverCharge'), session.get('crnLimitBy'), session.get('crnUserGroup'), session.get('crnTerm'), session.get('crnAutoQuotaSetup'))
        if addStatus == True:
            return render_template('message.html', alertLevel="success",
                                   message="Successfully added students from CRN:" + session.get('crnClass'), returnurl="/adduser")
        # elif addStatus == False:
        else:
            return render_template('message.html', alertLevel="error",
                                   message="Failed to add students from CRN:" + session.get('crnClass') + " " + addStatus,
                                   returnurl="/adduser")

    if 'addtype' in request.form:
        addUserType = request.form['addtype']
        if addUserType == "classcrn":
            session['crnClass'] = request.form['crn']
            session['crnAccountBalance'] = request.form['AccountBalance']
            session['crnOverCharge'] = request.form['OverCharge']
            session['crnLimitBy'] = request.form['LimitBy']
            # session['crnUserGroup'] = request.form['userGroup']
            term = str(request.form['wmuTerm']).replace("[", "").replace("]", "").replace("'", "").split(",")
            session['crnUserGroup'] = "CRN" + session.get('crnClass') + " -" + term[1]
            session['crnTerm'] = term[0]
            try:
                session['crnAutoQuotaSetup'] = request.form['autoQuotaSetup']
            except:
                session['crnAutoQuotaSetup'] = False

            '''Check the values received to make sure it's valid input'''
            checkValues = checkInputArray([[session.get('crnAccountBalance'), "float", "Account Balance"], [session.get('crnOverCharge'), "float", "Overcharge Factor"]],"/adduser")
            if checkValues != True:
                return checkValues

            session['crnlookup'] = True
            return render_template('loading.html', message="Looking up users. Please wait...", redirecturl="/adduser", waittime=0)

        elif addUserType == "singleuser":
            username = request.form['username']
            email = request.form['Email']
            description = request.form['Description']
            accountBalance = request.form['AccountBalance']
            overCharge = request.form['OverCharge']
            limitBy = request.form['LimitBy']
            try:
                autoQuotaSetup = request.form['autoQuotaSetup']
            except:
                autoQuotaSetup = False

            '''Check the values received to make sure it's valid input'''
            checkValues = checkInputArray([[accountBalance, "float", "Account Balance"],[overCharge, "float", "Overcharge Factor"]], "/adduser")
            if checkValues != True:
                return checkValues

            addStatus = pyKotaMan.addNewUser(username, email, description, accountBalance, overCharge, limitBy, autoQuotaSetup)
            if addStatus == True:
                return render_template('message.html', alertLevel="success", message="The following users were successfully added: " + username, returnurl="/adduser")
            elif addStatus == False:  
                return render_template('message.html', alertLevel="error", message="The following user already exists. Failed to add: " + username, returnurl="/adduser")
        return redirect("/adduser")
    else:
        return render_template('users/adduser.html',
                               config=config,
                               wmuCurrentTerm=pyKotaMan.ldap.getCurrentTermName(),
                               terms=pyKotaMan.ldap.getAllTerms())

@app.route("/edituser", methods=['POST', 'GET'])
@register_menu(app, '.users.edituser', 'Edit User(s)', order=1)
def edituser():
    if not session.get('logged_in'):
        return redirect("/")
    
    if "userid" in request.form or session.get('lookupuser') != None:
        try:
            userId = request.form['userid']
        except:
            userId = session.get('lookupuser')
        if userId == "*" or userId == "":
            lookupUsers = pyKotaMan.getAllUsers()
        else:
            lookupUsers = [ pyKotaMan.storage.getUser(userId) ]
            if lookupUsers[0].Email == None and lookupUsers[0].Description == None and lookupUsers[0].AccountBalance == None and lookupUsers[0].LifeTimePaid == None:
                return render_template('message.html', alertLevel="error", message="The following user doesn't exists: " + userId, returnurl="/edituser")
        return render_template('users/edituser.html', users=lookupUsers, returnurl="/edituser", summaryview="edit")
    else:
        lookupUsers = pyKotaMan.getAllUsers()
        return render_template('users/edituser.html', users=lookupUsers, returnurl="/edituser", summaryview="edit")

@app.route("/deluser", methods=['POST', 'GET'])
@register_menu(app, '.users.deluser', 'Batch Delete', order=2)
def deluser():
    if not session.get('logged_in'):
        return redirect("/")
    
    # '''Delete by class CRN'''
    # if "classcrn" in request.form:
    #     classCRN = request.form['classcrn']
    #     deletedUsers = pyKotaMan.deleteUsersByClassCRN(classCRN)
    #     if deletedUsers == False:
    #         return render_template('message.html', alertLevel="error", message="Failed to delete users. See log for details.", returnurl="/deluser")
    #     elif deletedUsers == "":
    #         return render_template('message.html', alertLevel="error", message="CRN not found. No users deleted.", returnurl="/deluser")
    #     else:
    #         usersDeleted = str(deletedUsers).replace('u', '').replace("'", '').replace('[', '').replace(']', '')
    #         return render_template('message.html', alertLevel="success", message="The following users were successfully deleted: " + usersDeleted, returnurl="/deluser")
    
    '''Delete users in group'''
    if "groupid" in request.form:
        curGroups = pyKotaMan.storage.getAllGroupsNames()
        groupId = request.form['groupid']
        if groupId not in curGroups:
            return render_template('message.html', alertLevel='error', message="The group " + groupId + " does not exist. No users deleted.", returnurl='/deluser', includeUserSummary=False)
        else:
            pyKotaMan.deleteAllUsersFromGroup(groupId)
            pyKotaMan.storage.getGroup(groupId).delete()
            return render_template('message.html', alertLevel='success', message="All users were successfully deleted from group " + groupId, returnurl='/deluser', includeUserSummary=False)
    
    '''Delete users by list'''
    if "usernames" in request.form:
        userNamesToDelete = request.form['usernames'].strip().split(',')
        allUserNames = pyKotaMan.storage.getAllUsersNames()
        for userName in userNamesToDelete:
            if userName.strip() == "":
                return redirect("/deluser")
            elif userName not in allUserNames:
                users = pyKotaMan.getAllUsers()
                return render_template('message.html', alertLevel="error", message=(userName + " not found! Failed to delete any users!"), returnurl="/deluser", includeUserSummary=False, users=users, sorton=session.get('sorton'), summaryview='read')
        
        '''Actually delete the users'''
        for userName in userNamesToDelete:
            delUser = pyKotaMan.storage.getUser(userName)
            log.log("DELETED USER: " + str(delUser.Name) + " " + str(delUser.Email) + " " + str(delUser.Description))
            delUser.delete()
        users = pyKotaMan.getAllUsers()
        #usersDeleted = str(userNamesToDelete).replace('u', '').replace("'", '').replace('[', '').replace(']', '')
        return render_template('message.html', alertLevel="success", message=("The following users were deleted successfully: " + arrayToString(userNamesToDelete)), returnurl="/deluser", includeUserSummary=False, users=users, sorton=session.get('sorton'), summaryview='read')
    #users = pyKotaMan.getAllUsers()
    return render_template('users/deluser.html', returnurl="/deluser")

@app.route("/saveusers", methods=['POST'])
def saveusers():
    if not session.get('logged_in'):
        return redirect("/")
    try:
        request.form['username2']
        numberOfUsers = pyKotaMan.getNumberOfUsers()
        #returnString = "/edituser?username=*"
    except:
        numberOfUsers = 1
        session['lookupuser'] = request.form['username1']
        #returnString = "/edituser?username=" + str(request.form['username1'])
        
    for i in range(1,numberOfUsers + 1):
        userName = request.form['username' + str(i)]
        newEmail = request.form['Email' + str(i)]
        newDescription = request.form['Description' + str(i)]
        newAccountBalance = request.form['AccountBalance' + str(i)]
        newOverCharge = request.form['OverCharge' + str(i)]
        newLimitBy = request.form['LimitBy' + str(i)]

        '''Check the values received to make sure it's valid input'''
        checkValues = checkInputArray([[newAccountBalance, "float", "Account Balance"], [newOverCharge, "float", "Overcharge Factor"]], "/edituser")
        if checkValues != True:
            return checkValues

        lookupUser = pyKotaMan.storage.getUser(userName)
        if newEmail != "":
            lookupUser.setEmail(newEmail)
        if newDescription != "":
            lookupUser.setDescription(newDescription)
        if newAccountBalance != "":
            newAccountBalance = float(int(newAccountBalance))
            lookupUser.setAccountBalance(newAccountBalance, lookupUser.LifeTimePaid + ( newAccountBalance - lookupUser.AccountBalance ))
        if newOverCharge != "":
            newOverCharge = float(int(newOverCharge))
            lookupUser.setOverChargeFactor(newOverCharge)
        if newLimitBy != lookupUser.LimitBy:
            lookupUser.setLimitBy(newLimitBy)
        if ("delete" + str(i)) in request.form:
            log.log(session.get('admininfo') + "DELETED USER: " + str(lookupUser.Name) + " " + str(lookupUser.Email) + " " + str(lookupUser.Description))
            lookupUser.delete()
            session['lookupuser'] = None
        if lookupUser.Exists == True and lookupUser.isDirty == True:
            log.log("USER INFO UPDATED: " + userName + " : " + newEmail + " : " + newDescription + " : " + str(newAccountBalance) + " : " + str(newOverCharge) + " : " + newLimitBy)
        lookupUser.save()
    return redirect("/edituser")

@app.route("/groups", methods=['POST', 'GET'])
@register_menu(app, ".groups", "Groups", order=1)
def groups():
    if not session.get('logged_in'):
        return redirect("/")
    groups = pyKotaMan.getAllGroups()
    for group in groups:
        if ( "view" + group.Name ) in request.form:
            session['viewgroup'] = group.Name
    if session.get('viewgroup') != None:
        users = pyKotaMan.storage.getGroupMembers(pyKotaMan.storage.getGroup(session.get('viewgroup')))
        return render_template('groups/groups.html', groups=groups, summaryview='read', users=users, summarytitle="Members of " + group.Name, returnurl='/groups')
    return render_template('groups/groups.html', groups=groups, summaryview='read' )

@app.route("/addgroup", methods=['POST', 'GET'])
@register_menu(app, '.groups.addgroup', 'Add Group(s)', order=0)
def addgroup():
    if not session.get('logged_in'):
        return redirect("/")
    
    if "addtype" in request.form:
        addType = request.form['addtype']
        if addType == "single":
            groupId = request.form['groupid']
            description = request.form['description']
            limitBy = request.form['LimitBy']
            pyKotaMan.addNewGroup(groupId, description, limitBy)
            #if newGroup == False:
            #    return render_template('message.html', alertLevel="error", message=("The following groups already exist. Failed to add new group: " + groupId), returnurl="/addgroup", includeUserSummary=False)
            #else:
            #    return render_template('message.html', alertLevel="success", message=("The following groups were added successfully: " + groupId), returnurl="/addgroup", includeUserSummary=False)
            
    groups = pyKotaMan.getAllGroups()
    return render_template('groups/addgroup.html', groups=groups, summaryview='read')

@app.route("/editgroup", methods=['POST', 'GET'])
@register_menu(app, '.groups.editgroup', 'Edit Group(s)', order=1)
def editgroup():
    if not session.get('logged_in'):
        return redirect("/")
    groups = pyKotaMan.getAllGroups()
    
    if session.get('editgroup') != None:
        group = pyKotaMan.storage.getGroup(session.get('editgroup'))
        users = pyKotaMan.storage.getGroupMembers(group)
        return render_template('groups/editgroup.html', groups=groups, summaryview='edit', users=users, summarytitle="Members of " + group.Name)
    
    return render_template('groups/editgroup.html', groups=groups, summaryview='edit')

@app.route("/savegroups", methods=['POST'])
def savegroups():
    if not session.get('logged_in'):
        return redirect("/")
    
    '''Delete users from a group'''
    if session.get('editgroup') != None and "deleteuserfromgroup" in request.form:
        deletedUsers = []
        numberOfUsers = pyKotaMan.getNumberOfUsersInGroup(session.get('editgroup'))
        for i in range(1, numberOfUsers + 1):
            if ( "delete" + str(i) ) in request.form:
                delUserId = request.form["userid" + str(i)]
                deletedUsers.append(delUserId)
                pyKotaMan.deleteUserFromGroup(session.get('editgroup'), delUserId)
                
        
        return redirect("/editgroup")
    
    '''Adding users to a group'''
    if "adduserids" in request.form:
        userids = request.form['adduserids'].strip().split(",")
        curUserids = pyKotaMan.storage.getAllUsersNames()
        for userid in userids:
            if userid not in curUserids:
                return render_template('message.html', alertLevel="error", message=("Failed to add users to group. The following user does not exist: " + userid), returnurl="/editgroup", includeUserSummary=False)
            else:
                pyKotaMan.addUserToGroup(userid, session.get('addgroup'))
        usernames = str(userids).replace('u', '').replace("'", '').replace('[', '').replace(']', '')
        return render_template('message.html', alertLevel="success", message=("The following users were added to group " + session.get('addgroup') + ": " + usernames), returnurl="/editgroup", includeUserSummary=False)
    
    '''set the group to add or edit'''
    groups = pyKotaMan.getAllGroups()
    for group in groups:
        if ( "edit" + group.Name ) in request.form:
            session['editgroup'] = group.Name
            session['addgroup'] = None
            return redirect("/editgroup")
        elif ( "add" + group.Name ) in request.form:
            session['addgroup'] = group.Name
            session['editgroup'] = None
            return redirect("/editgroup")
    
    '''Save changes to groups'''
    try:
        request.form['groupid2']
        numberOfGroups = pyKotaMan.getNumberOfGroups()
    except:
        numberOfGroups = 1
        
    for i in range(1,numberOfGroups + 1):
        groupId = request.form['groupid' + str(i)]
        newDescription = request.form['Description' + str(i)]
        newLimitBy = request.form['LimitBy' + str(i)]
        lookupGroup = pyKotaMan.storage.getGroup(groupId)
        if newDescription != "":
            lookupGroup.setDescription(newDescription)
        
        if newLimitBy != lookupGroup.LimitBy:
            lookupGroup.setLimitBy(newLimitBy)
        if ("delete" + str(i)) in request.form:
            lookupGroup.delete()
        if lookupGroup.Exists == True and lookupGroup.isDirty == True:
            log.log("GROUP INFO UPDATED: " + groupId + " : " + newDescription + " : " + newLimitBy)
        lookupGroup.save()
    return redirect("/editgroup")
    
@app.route("/printers")
@register_menu(app, ".printers", "Printers", order=2)
def printers():
    if not session.get('logged_in'):
        return redirect("/")
    printers = pyKotaMan.getAllPrinters()
    return render_template('printers/printers.html', printers=printers)

@app.route("/addprinter", methods=['POST', 'GET'])
@register_menu(app, '.printers.addprinter', 'Add Printer(s)', order=0)
def addprinter():
    if not session.get('logged_in'):
        return redirect("/")
    
    '''Add a new printer'''
    if "addprinter" in request.form:
        printerId = request.form['Name']
        pricePerPage = request.form['PricePerPage']
        pricePerJob = request.form['PricePerJob']
        maxJobSize = request.form['MaxJobSize']
        passthroughMode = request.form['PassthroughMode']

        '''Check the values received to make sure it's valid input'''
        checkValues = checkInputArray([[pricePerPage, "float", "Price Per Page"], [pricePerJob, "float", "Price Per Job"], [maxJobSize, "int", "Max Job Size"]], "/addprinter")
        if checkValues != True:
            return checkValues

        addStatus = pyKotaMan.addPrinter(printerId, pricePerPage, pricePerJob, maxJobSize, stringToBool(passthroughMode))
        if addStatus == False:
            return render_template('message.html', alertLevel="error", message="Failed to add printer " + printerId + ". Printer already exists.", returnurl="/addprinter", includeUserSummary=False)
        else:
            return render_template('message.html', alertLevel='success', message="The following printers were successfully added: " + printerId, returnurl='/addprinter', includeUserSummary=False)
    
    return render_template('printers/addprinter.html')

@app.route("/editprinter", methods=['POST', 'GET'])
@register_menu(app, '.printers.editprinter', 'Edit Printer(s)', order=1)
def editprinter():
    if not session.get('logged_in'):
        return redirect("/")
    printers = pyKotaMan.getAllPrinters()
    return render_template('printers/editprinter.html', printers=printers, summaryview='edit')

@app.route("/saveprinters", methods=['POST'])
def saveprinters():
    if not session.get('logged_in'):
        return redirect("/")

    '''Save changes to printers'''
    try:
        request.form['printerid2']
        numberOfPrinters = pyKotaMan.getNumberOfPrinters()
    except:
        numberOfPrinters = 1
    for i in range(1, numberOfPrinters + 1):
        printerId = request.form['printerid' + str(i)]
        pricePerPage = request.form['PricePerPage' + str(i)]
        pricePerJob = request.form['PricePerJob' + str(i)]
        maxJobSize = request.form['MaxJobSize' + str(i)]
        passthroughMode = stringToBool(request.form['PassthroughMode' + str(i)])

        '''Check the values received to make sure it's valid input'''
        checkValues = checkInputArray([ [ pricePerPage, "float", "Price Per Page" ], [ pricePerJob, "float", "Price Per Job" ], [ maxJobSize, "int", "Max Job Size"] ], "/editprinter")
        if checkValues != True:
            return checkValues

        lookupPrinter = pyKotaMan.storage.getPrinter(printerId)
        if pricePerPage != "":
            lookupPrinter.setPrices(pricePerPage, lookupPrinter.PricePerJob)
        if pricePerJob != "":
            lookupPrinter.setPrices(lookupPrinter.PricePerPage, pricePerJob)
        if maxJobSize != "":
            lookupPrinter.setMaxJobSize(maxJobSize)
        if passthroughMode != lookupPrinter.PassThrough:
            lookupPrinter.setPassThrough(passthroughMode)
        if ("delete" + str(i)) in request.form:
            lookupPrinter.delete()
        if lookupPrinter.Exists == True and lookupPrinter.isDirty == True:
            log.log("PRINTER INFO UPDATED: " + printerId + " : " + str(pricePerPage) + " : " + str(pricePerJob) + " : " + str(maxJobSize) + " : " + str(passthroughMode))
        lookupPrinter.save()
    return redirect("/editprinter")

@app.route("/quotas", methods=['POST', 'GET'])
@register_menu(app, '.quotas', 'Quotas', order=3)
def quotas():
    if not session.get('logged_in'):
        return redirect("/")
    quotas = pyKotaMan.getAllQuotas()
    return render_template('quotas/quotas.html', quotas=quotas, summaryview='read', summarytype='Printer')

@app.route("/printerquotas", methods=['POST', 'GET'])
@register_menu(app, '.quotas.printerquotas', 'Printer Quotas', order=0)
def printerquotas():
    if not session.get('logged_in'):
        return redirect("/")
    printers = pyKotaMan.getAllPrinters()
    printerQuotaGroupMembers = None
    printerQuotaUserMembers = None

    if "printerId" in request.form:
        printerId = request.form['printerId']
        if "edit" in request.form:
            printerQuotaGroupMembers = pyKotaMan.getAllPrinterQuotaGroupMembers(printerId)
            printerQuotaUserMembers = pyKotaMan.getAllPrinterQuotaUserMembers(printerId)
            session['editprinterquota'] = printerId
            session['addprinterquota'] = None
        elif "add" in request.form:
            session['addprinterquota'] = printerId
            session['editprinterquota'] = None
    return render_template('quotas/printerquotas.html', printers=printers, printerQuotaGroupMembers=printerQuotaGroupMembers, printerQuotaUserMembers=printerQuotaUserMembers)

@app.route("/groupquotas", methods=['POST', 'GET'])
@register_menu(app, '.quotas.groupquotas', 'Group Quotas', order=1)
def groupquotas():
    if not session.get('logged_in'):
        return redirect("/")
    quotas = pyKotaMan.getAllGroupPrinterQuotas()
    return render_template('quotas/groupquotas.html', quotas=quotas, summaryview='edit', summarytype='Group')

@app.route("/userquotas", methods=['POST', 'GET'])
@register_menu(app, '.quotas.userquotas', 'User Quotas', order=2)
def userquotas():
    if not session.get('logged_in'):
        return redirect("/")
    quotas = pyKotaMan.getAllUserPrinterQuotas()
    return render_template('quotas/userquotas.html', quotas=quotas, summaryview='edit', summarytype='User')

@app.route("/savequotas", methods=['POST'])
def savequotas():
    if not session.get('logged_in'):
        return redirect("/")

    '''Delete users from a printer'''
    if "deleteusers" in request.form:
        printerId = session.get('editprinterquota')
        numberOfUsers = len(pyKotaMan.getAllPrinterQuotaUserMembers(printerId))
        deletedUsers = []
        for i in range(1, numberOfUsers + 1):
            if ( "delete" + str(i) ) in request.form:
                delUserId = request.form['userId' + str(i)]
                pyKotaMan.deleteUserPrinterQuota(printerId, delUserId)
                deletedUsers.append(delUserId)
        return render_template('message.html', alertLevel="success", message=("The following users were deleted from " + printerId + "'s Quota: " + arrayToString(deletedUsers)), returnurl="/printerquotas", includeUserSummary=False)

    '''Delete groups from a printer'''
    if "deletegroups" in request.form:
        printerId = session.get('editprinterquota')
        numberOfGroups = len(pyKotaMan.getAllPrinterQuotaGroupMembers(printerId))
        deletedGroups = []
        for i in range(1, numberOfGroups + 1):
            if ( "delete" + str(i) ) in request.form:
                delGroupId = request.form['groupId' + str(i)]
                pyKotaMan.deleteGroupPrinterQuota(printerId, delGroupId)
                deletedGroups.append(delGroupId)
        return render_template('message.html', alertLevel="success", message=("The following groups were deleted from " + printerId + "'s Quota: " + arrayToString(deletedGroups)), returnurl="/printerquotas",includeUserSummary=False)

    '''Add users and groups to a printer'''
    if "addusergroupquotas" in request.form:
        printerId = session.get('addprinterquota')
        addIds = request.form['addids'].strip().split(',')
        groups = pyKotaMan.storage.getAllGroupsNames()
        users = pyKotaMan.storage.getAllUsersNames()
        for id in addIds:
            if id in groups:
                pyKotaMan.addGroupPrinterQuota(printerId, id)
            elif id in users:
                pyKotaMan.addUserPrinterQuota(printerId, id)
            else:
                return render_template('message.html', alertLevel='error', message=("The following user or group does not exist and was not added to the printer quota: " + id), returnurl='/printerquotas', includeSummary=False)
        return render_template('message.html', alertLevel='success', message=("The following users or groups were successfully added to " + printerId +"'s quota: " + arrayToString(addIds)), returnurl='/printerquotas', includeSummary=False)

    '''Save a user or group quota'''
    if "saveusergroupquota" in request.form:
        if "groupId1" in request.form:
            numberOfQuotas = len(pyKotaMan.getAllGroupPrinterQuotas())
        else:
            numberOfQuotas = len(pyKotaMan.getAllUserPrinterQuotas())
        print numberOfQuotas
        for i in range(1, numberOfQuotas + 1):
            printerId = request.form['printerId' + str(i)]
            if ( "groupId" + str(i) ) in request.form:
                groupId = request.form['groupId' + str(i)]
                quota = pyKotaMan.getGroupPrinterQuota(printerId, groupId)
                quotaName = quota.Group.Name
                redirectString = "/groupquotas"
            elif ( "userId" + str(i) ) in request.form:
                userId = request.form['userId' + str(i)]
                quota = pyKotaMan.getUserPrinterQuota(printerId, userId)
                quotaName = quota.User.Name
                redirectString = "/userquotas"
            softLimit = request.form['SoftLimit' + str(i)]
            hardLimit = request.form['HardLimit' + str(i)]
            dateLimit = request.form['DateLimit' + str(i)]

            '''Check the values received to make sure it's valid input'''
            checkValues = checkInputArray([[softLimit, "int", "Soft Limit"], [hardLimit, "int", "Hard Limit"], [dateLimit, "date", "Date Limit"]], redirectString)
            if checkValues != True:
                return checkValues

            if softLimit != "":
                quota.setLimits(softLimit, quota.HardLimit)
            if hardLimit != "":
                quota.setLimits(quota.SoftLimit, hardLimit)
            if dateLimit != "":
                quota.setDateLimit(dateLimit)
            if quota.Exists == True and quota.isDirty == True:
                log.log("QUOTA INFO UPDATED: " + quotaName + " : " + str(softLimit) + " : " + str(hardLimit) + " : " + str(dateLimit))
            quota.save()
        return redirect(redirectString)

@app.route("/sorton", methods=['POST'])
def sorton():
    if not session.get('logged_in'):
        return redirect("/")
    sorton = request.form['sorton'].replace(' ', '')
    if sorton == "UserID":
        sorton = "Name"
    if sorton == "OverchargeFactor":
        sorton = "OverCharge"
    session['sorton'] = sorton
    return redirect(request.form['returnurl'])

@app.route("/login", methods=['POST'])
def login():
    session['clientip'] = request.remote_addr
    session['username'] = request.form['username']
    password = request.form['password']
    if password == "" or password == None:
        return render_template('message.html', alertLevel="error", message="Password cannot be blank.", returnurl="/")

    if config.getConfig("loginUseLdap") == "True":
        log.log("LOGIN REQUEST Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
        loginStatus = ld.login(session.get('username'), password)
        if loginStatus[0] == '1':
            session['logged_in'] = True
            session['name'] = ld.getName(session.get('username'))
            session['group'] = loginStatus[1]
            log.log("LOGIN SUCCESS Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
        else:
            log.log("LOGIN FAILURE Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
            return render_template('message.html', alertLevel="error", message=loginStatus[1], returnurl="/")
    else:
        if session.get('username') == config.getConfig("localAdminUsername"):
            log.log("ADMIN LOGIN REQUEST Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
            if password == config.getConfig("localAdminPassword"):
                session['logged_in'] = True
                session['name']  = "Built in Administrator"
                session['group'] = "PyKota Administrators"
                log.log("ADMIN LOGIN SUCCESS Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
            else:
                log.log("ADMIN LOGIN FAILURE Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
                return render_template('message.html', alertLevel="error", message="Bad Password.", returnurl="/")
        else:
            log.log("ADMIN LOGIN FAILURE Client IP: " + session.get('clientip') + " Username: " + session.get('username') )
            return render_template('message.html', alertLevel="error", message="Bad Username.", returnurl="/")
    return redirect("/")

@app.route("/settings", methods=['POST', 'GET'])
@register_menu(app, '.settings', 'Settings', order=4)
def settings():
    if not session.get('logged_in'):
        return redirect("/")

    '''Save settings'''
    if "savesettings" in request.form:
        newSettings = request.form.to_dict()
        curSettings = config.getAllSettings()
        newSettings.pop('savesettings')
        for key in curSettings:
            if key not in newSettings:
                newSettings[key] = "False"
        for key in newSettings:
            if newSettings.get(key) == 'on':
                newSettings[key] = 'True'
            if newSettings.get(key) == "" or newSettings.get(key) == None:
                newSettings[key] = curSettings.get(key)
        config.setAllSettings(newSettings)
        log.log("SETTINGS UPDATED: " + str(newSettings))
        return render_template('loading.html', message="Restarting PyKota Web Admin to apply changes...", redirecturl="/restart", waittime=0)

    return render_template('settings.html', config=config)

@app.route("/about")
@register_menu(app, '.about', 'About', order=5)
def about():
    if not session.get('logged_in'):
        return redirect("/")
    cupsVersion = commands.getoutput("cups-config --version")
    return render_template('about.html', git=Git.Git(), cupsVersion=cupsVersion)

@app.route("/logout")
@register_menu(app, '.logout', 'Logout', order=6)
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect("/")

@app.route("/restart")
def restart():
    if not session.get('logged_in'):
        return redirect("/")
    os.system("sleep 5 && " + config.getConfigRoot() + "/pykotawebadmin.init start &")
    os.system(config.getConfigRoot() + "/pykotawebadmin.init stop &")
    return render_template('loading.html', message="Restarting PyKota Web Admin to apply changes...", redirecturl="/", waittime=4)

def stringToBool(testString):
    testString = testString.lower()
    if testString == "true":
        return True
    else:
        return False

def arrayToString(array):
    returnString = ""
    for a in array:
        returnString = returnString + str(a) + ", "
    return returnString[:-2]

def checkInputType(inputValue, type):
    if inputValue == "" :
        return True
    if type == "float":
        if inputValue == "0":
            return True
        try:
            float(inputValue)
            return True
        except:
            return "Must be floating point number."
    elif type == "int":
        if inputValue == "0":
            return True
        try:
            int(inputValue)
            return True
        except:
            return "Must be integer."
    elif type == "date":
        try:
            DateTime.ISO.ParseDateTime(str(inputValue)[:19])
            return True
        except:
            return "Must be formatted as YYYY-MM-DD HH:MM:SS"

'''[ [ inputValue, inputType, inputDescription ], ... ]'''
def checkInputArray(inputValueArray, returnurl):
    for inputValue in inputValueArray:
        inputCheck = checkInputType(inputValue[0], inputValue[1])
        if inputCheck != True:
            return render_template('message.html', alertLevel='error', message="Bad input received for " + inputValue[2] + ". " + inputCheck, returnurl=returnurl)
    return True

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    if config.getConfig("enableSSL") == "True":
        app.run(debug=stringToBool(config.getConfig("flaskWebDebug")), host='0.0.0.0', port=int(config.getConfig("serverListenPort")), threaded=True, ssl_context=context)
    else:
        app.run(debug=stringToBool(config.getConfig("flaskWebDebug")), host='0.0.0.0', port=int(config.getConfig("serverListenPort")), threaded=True)
    
    
    
    