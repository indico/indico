# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.


"""
LDAP authentication for Indico

Generously contributed by Martin Kuba <makub@ics.muni.cz>
Improved/maintained by the Indico Team

This code expects a simple LDAP structure with users on one level like:

dn: uid=john,ou=people,dc=example,dc=com
objectClass: inetOrgPerson
uid: john
cn: John Doe
mail: john@example.com
o: Example Inc.
postalAddress: Example Inc., Some City, Some Country

and groups in the OpenLDAP/SLAPD format listing their members by DNs, like:

dn: cn=somegroup,ou=groups,dc=example,dc=com
objectClass: groupOfNames
cn: somegroup
member: uid=john,ou=people,dc=example,dc=com
member: uid=alice,ou=people,dc=example,dc=com
member: uid=bob,ou=people,dc=example,dc=com
description: Just a group of people ...

or groups in ActiveDirectory format marked by 'memberof' attribute.

Adjust it to your needs if your LDAP structure is different,
preferably by changing the extractUserDataFromLdapData() method.

See indico.conf for information about customization options.
"""

# python-ldap
try:
    import ldap
    import ldap.filter
    import re
except:
    pass

from urlparse import urlparse

# legacy indico imports
from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity, SSOHandler
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger
from indico.core import config as Configuration
from MaKaC.user import Group, PrincipalHolder


RETRIEVED_FIELDS = ['uid', 'cn', 'mail', 'o', 'ou', 'company', 'givenName',
                    'sn', 'postalAddress', 'userPrincipalName', "telephoneNumber", "facsimileTelephoneNumber"]
UID_FIELD = "cn"  # or uid
MEMBER_ATTR = "member"
MEMBER_PAGE_SIZE = 1500


class LDAPAuthenticator(Authenthicator, SSOHandler):
    idxName = "LDAPIdentities"
    id = 'LDAP'
    name = 'LDAP'
    description = "LDAP Login"

    _operations = {
    'email': '(mail={0})',
    'name': '(givenName={0})',
    'surName': '(sn={0})',
    'organisation': '(|(o={0})(ou={0}))',
    'login': '(cn={0})'
    }

    def __init__(self):
        Authenthicator.__init__(self)

    def canUserBeActivated(self):
        return True

    def createIdentity(self, li, avatar):
        Logger.get("auth.ldap").info("createIdentity %s (%s %s)" % (li.getLogin(), avatar.getId(), avatar.getEmail()))
        if self.checkLoginPassword(li.getLogin(), li.getPassword()):
            return LDAPIdentity(li.getLogin(), avatar)
        else:
            return None

    def createIdentitySSO(self, login, avatar):
        Logger.get("auth.ldap").info("createIdentitySSO %s (%s %s)" % (login, avatar.getId(), avatar.getEmail()))
        return LDAPIdentity(login, avatar)

    def fetchIdentity(self, avatar):
        Logger.get("auth.ldap").info("fetchIdentity (%s %s)" % (avatar.getId(), avatar.getEmail()))
        user = self.matchUser({"email": avatar.getEmail()}, exact=1)
        if user:
            user = user.values()[0]
            identity = LDAPIdentity(user["login"], avatar)
            self.add(identity)
            return identity
        return None

    def createUser(self, li):
        Logger.get('auth.ldap').debug("create '%s'" % li.getLogin())
        # first, check if authentication is OK
        data = self.checkLoginPassword(li.getLogin(), li.getPassword())
        if not data:
            return None

        # Search if user already exist, using email address
        import MaKaC.user as user
        ah = user.AvatarHolder()
        userList = ah.match({"email": data["mail"]}, searchInAuthenticators=False)
        if len(userList) == 0:
            # User doesn't exist, create it
            try:
                av = user.Avatar()
                udata = LDAPTools.extractUserDataFromLdapData(data)
                av.setName(udata['name'])
                av.setSurName(udata['surName'])
                av.setOrganisation(udata['organisation'])
                av.setEmail(udata['email'])
                av.setAddress(udata['address'])
                ah.add(av)
                av.activateAccount()
                Logger.get('auth.ldap').info("created '%s'" % li.getLogin())
            except KeyError:
                raise MaKaCError("LDAP account does not contain the mandatory"
                                 "data to create an Indico account.")
        else:
            # user founded
            Logger.get('auth.ldap').info("found user '%s'" % li.getLogin())
            av = userList[0]
        #now create the LDAP identity for the user
        na = LDAPAuthenticator()
        id = na.createIdentity(li, av)
        na.add(id)
        return av

    def matchUser(self, criteria, exact=0):
        criteria = dict((k, ldap.filter.escape_filter_chars(v)) \
                        for k, v in criteria.iteritems() if v.strip() != '')
        lfilter = list((self._operations[k].format(v if exact else ("*%s*" % v))) \
                       for k, v in criteria.iteritems())

        if lfilter == []:
            return {}
        ldapc = LDAPConnector()
        ldapc.open()
        fquery = "(&%s)" % ''.join(lfilter)
        d = ldapc.findUsers(fquery)
        ldapc.close()
        return d

    def matchUserFirstLetter(self, index, letter):
        lfilter = self._operations[index].format("%s*" % letter)
        if lfilter == []:
            return {}
        ldapc = LDAPConnector()
        ldapc.open()
        fquery = "(&%s)" % ''.join(lfilter)
        d = ldapc.findUsers(fquery)
        ldapc.close()
        return d

    def searchUserById(self, id):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.lookupUser(id)
        ldapc.close()
        if(ret == None):
            return None
        av = LDAPTools.dictToAv(ret)
        av["id"] = id
        av["identity"] = LDAPIdentity
        av["authenticator"] = LDAPAuthenticator()
        Logger.get('auth.ldap').debug('LDAPUser.getById(%s) return %s '%(id,av))
        return av

    def checkLoginPassword(self, userName, password):
        if not password or not password.strip():
            Logger.get('auth.ldap').info("Username: %s - empty password" % userName)
            return None
        try:
            ret = {}
            ldapc = LDAPConnector()
            ldapc.openAsUser(userName, password)
            ret = ldapc.lookupUser(userName)
            ldapc.close()
            Logger.get('auth.ldap').debug("Username: %s checked: %s" % (userName, ret))
            if not ret :
                return None
            #LDAP search is case-insensitive, we want case-sensitive match
            if ret.get(UID_FIELD)!=userName :
                Logger.get('auth.ldap').info('user %s invalid case %s' % (userName,ret.get(UID_FIELD)))
                return None
            return ret
        except ldap.INVALID_CREDENTIALS:
            Logger.get('auth.ldap').info("Username: %s - invalid credentials" % userName)
            return None

    def matchGroup(self, criteria, exact=0):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.findGroups(ldap.filter.escape_filter_chars(criteria), exact)
        ldapc.close()
        groupList = []
        for grDict in ret:
            grName = grDict['cn']
            gr = LDAPGroup()
            gr.setId(grName)
            gr.setName(grName)
            gr.setDescription('LDAP group: ' + grDict.get('description',''))
            groupList.append(gr)
        return groupList

    def matchGroupFirstLetter(self, letter):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.findGroupsFirstLetter(ldap.filter.escape_filter_chars(letter))
        ldapc.close()
        groupList = []
        for grDict in ret:
            grName = grDict['cn']
            gr = LDAPGroup()
            gr.setId(grName)
            gr.setName(grName)
            gr.setDescription('LDAP group: ' + grDict.get('description',''))
            groupList.append(gr)
        return groupList

    def getGroupMemberList(self, group):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.findGroupMemberUids(group)
        ldapc.close()
        return ret

    def isUserInGroup(self, user, group):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.userInGroup(user, group)
        ldapc.close()
        return ret

class LDAPIdentity(PIdentity):

    def __str__(self):
        return '<LDAPIdentity{login:%s, tag:%s}>' % \
               (self.getLogin(), self.getAuthenticatorTag())

    def authenticate(self, id):
        """
        id is MaKaC.user.LoginInfo instance, self.user is Avatar
        """

        log = Logger.get('auth.ldap')
        log.info("authenticate(%s)" % id.getLogin())
        data = AuthenticatorMgr().getById(self.getAuthenticatorTag()).checkLoginPassword(id.getLogin(),
                                                                                                     id.getPassword())
        if not data or self.getLogin() != id.getLogin():
            return None
        # modify Avatar with the up-to-date info from LDAP
        av = self.user
        av.clearAuthenticatorPersonalData()
        udata = LDAPTools.extractUserDataFromLdapData(data)

        mail = udata.get('email', '').strip()
        if mail != '' and mail != av.getEmail():
            av.setEmail(mail, reindex=True)
        av.setAuthenticatorPersonalData('firstName', udata.get('name'))
        av.setAuthenticatorPersonalData('surName', udata.get('surName'))
        av.setAuthenticatorPersonalData('affiliation', udata.get('organisation'))
        av.setAuthenticatorPersonalData('address', udata.get('address'))
        av.setAuthenticatorPersonalData('phone', udata.get('phone'))
        av.setAuthenticatorPersonalData('fax', udata.get('fax'))
        return self.user

    def getAuthenticatorTag(self):
        return LDAPAuthenticator.getId()


class LDAPConnector(object):
    """
    handles communication with the LDAP server specified in indico.conf
    default values as specified in Configuration.py are
     * host="ldap.example.com"
     * peopleDN="ou=people,dc=example,dc=com"
     * groupsDN="ou=groups,dc=example,dc=com"

    the code expects the users to be (in the LDAP) objects of type inetOrgPerson
    identified by thier "uid" attribute, and the groups to be objects of type
    groupOfNames with the "member" multivalued attribute containing complete DNs
    of users which seems to be the standard LDAP setup
    """

    def __init__(self):
        conf = Configuration.Config.getInstance()
        ldapConfig = conf.getAuthenticatorConfigById("LDAP")
        self.ldapUri = ldapConfig.get('uri')
        self.ldapPeopleFilter, self.ldapPeopleDN = \
                               ldapConfig.get('peopleDNQuery')
        self.ldapGroupsFilter, self.ldapGroupsDN = \
                               ldapConfig.get('groupDNQuery')
        self.ldapAccessCredentials = ldapConfig.get('accessCredentials')
        self.ldapUseTLS = ldapConfig.get('useTLS')
        self.groupStyle = ldapConfig.get('groupStyle')

    def login(self):
        try:
            self.l.bind_s(*self.ldapAccessCredentials)
        except ldap.INVALID_CREDENTIALS:
            raise Exception("Cannot login to LDAP server")

    def _findDN(self, dn, filterstr, param):
        result = self.l.search_s(dn, ldap.SCOPE_SUBTREE,
                               filterstr.format(param))

        for dn, data in result:
            if dn:
                # return just DN
                return dn

    def _findDNOfUser(self, userName):
        return self._findDN(self.ldapPeopleDN,
                            self.ldapPeopleFilter, userName)

    def _findDNOfGroup(self, groupName):
        return self._findDN(self.ldapGroupsDN,
                            self.ldapGroupsFilter, groupName)

    def open(self):
        """
        Opens an anonymous LDAP connection
        """
        self.l = ldap.initialize(self.ldapUri)
        self.l.protocol_version = ldap.VERSION3

        if self.ldapUseTLS:
            self.l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        else:
            self.l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_NEVER)

        if urlparse(self.ldapUri)[0] != "ldaps" and self.ldapUseTLS:
            self.l.start_tls_s()

        return self.l

    def openAsUser(self, userName, password):
        """
        Verifies username and password by binding to the LDAP server
        """
        self.open()
        self.login()

        dn = self._findDNOfUser(ldap.filter.escape_filter_chars(userName))

        if dn:
            self.l.simple_bind_s(dn, password)

    def close(self):
        """
        Closes LDAP connection
        """
        self.l.unbind_s()
        self.l = None

    def _objectAttributes(self, dn, result_data, attributeNames):
        """
        adds selected attributes
        """
        objectAttr = {'dn': dn}
        for name in attributeNames:
            self._addAttribute(objectAttr, result_data, name)
        return objectAttr


    def _addAttribute(self, objectAttr, attrMap, attrName):
        """
        safely adds attribute
        """
        if attrName in attrMap:
            attr = attrMap[attrName]
            if len(attr) == 1:
                objectAttr[attrName] = attr[0]
            else:
                objectAttr[attrName] = attr

    def lookupUser(self, uid):
        """
        Finds a user in LDAP
        Returns a map containing dn,cn,uid,mail,o,ou and postalAddress as
        keys and strings as values
        returns None if a user is not found
        """

        res = self.l.search_s(
            self.ldapPeopleDN, ldap.SCOPE_SUBTREE,
            self.ldapPeopleFilter.format(uid))

        for dn, data in res:
            if dn:
                Logger.get('auth.ldap').debug('lookupUser(%s) successful'%uid)
                return self._objectAttributes(dn, data, RETRIEVED_FIELDS)
        return None

    def findUsers(self, ufilter):
        """
        Finds users according to a specified filter
        """

        d = {}
        self.login()

        res = self.l.search_s(self.ldapPeopleDN, ldap.SCOPE_SUBTREE, ufilter)
        for dn, data in res:
            if dn:
                ret = self._objectAttributes(dn, data, RETRIEVED_FIELDS)
                av = LDAPTools.dictToAv(ret)
                d[ret['mail']] = av
        return d

    def _findGroups(self, gfilter):
        res = self.l.search_s(self.ldapGroupsDN, ldap.SCOPE_SUBTREE, gfilter)
        groupDicts = []
        for dn, data in res:
            if dn:
                groupDicts.append(self._objectAttributes(
                    dn, data, ['cn', 'description']))
        return groupDicts

    def findGroups(self, name, exact):
        """
        Finds a group in LDAP
        Returns an array of groups matching the group name, each group
        is represented by a map with keys cn and description
        """
        if exact == 0:
            star = '*'
        else:
            star = ''
        name = name.strip()
        if len(name) > 0:
            gfilter = self.ldapGroupsFilter.format(star + name + star)
        else:
            return []
        Logger.get('auth.ldap').debug('findGroups(%s) '%name)
        return self._findGroups(gfilter)


    def findGroupsFirstLetter(self, letter):
        """
        Finds a group in LDAP by the first letter
        Returns an array of groups matching the group name, each group
        is represented by a map with keys cn and description
        """
        if len(letter) == 1:
            gfilter = self.ldapGroupsFilter.format(letter + "*")
        else:
            return []
        Logger.get('auth.ldap').debug('findGroupsFirstLEtter(%s) '%letter)
        return self._findGroups(gfilter)

    def userInGroup(self, login, group):
        """
        Returns whether a user is in a group. Depends on groupStyle (SLAPD/ActiveDirectory)
        """
        Logger.get('auth.ldap').debug('userInGroup(%s,%s)' % (login, group))
        # In ActiveDirectory users have attribute 'tokenGroups' with list of groups Sids
        # In SLAPD groups have multivalues attribute 'member' with list of users
        if self.groupStyle == 'ActiveDirectory':
            groupSid = self.l.search_s(self._findDNOfGroup(group), ldap.SCOPE_BASE,
                                       attrlist=['objectSid'])[0][1]['objectSid'][0]
            res = self.l.search_s(self._findDNOfUser(login), ldap.SCOPE_BASE,
                                  attrlist=['tokenGroups'])[0][1]['tokenGroups']
            return groupSid in res
        elif self.groupStyle == 'SLAPD':
            query = 'member={0}'.format(self._findDNOfUser(login))
            res = self.l.search_s(self._findDNOfGroup(group), ldap.SCOPE_BASE, query)
            return res != []
        else:
            raise Exception("Unknown LDAP group style, choices are: SLAPD or ActiveDirectory")

    def nestedSearch(self, dnEgroup, visited):
        if dnEgroup in visited:
            return set()
        members = set()
        entries = []
        index = 0
        end_regex = '{0};range=[0-9]*-\*'.format(MEMBER_ATTR)
        while True:
            attr_filter = '{0};range={1}-{2}'.format(MEMBER_ATTR, index * MEMBER_PAGE_SIZE,
                                                     ((index+1) * MEMBER_PAGE_SIZE) - 1)
            member_found = self.l.search_s(dnEgroup, ldap.SCOPE_BASE, '(objectClass=Group)', [attr_filter])
            if not member_found:
                break
            if not member_found[0][1]:
                visited[dnEgroup] = True
                return members
            attr = member_found[0][1].keys()[0]
            entries += member_found[0][1][attr]
            if re.match(end_regex, attr):
                break
            index += 1

        if not entries:
            memberuid = LDAPTools.extractUIDFromDN(dnEgroup)
            if memberuid:
                members.add(memberuid)
        else:
            visited[dnEgroup] = True
            for member in entries:
                members.update(self.nestedSearch(member, visited))
        return members

    def findGroupMemberUids(self, group):
        """
         Finds uids of users in a group. Depends on groupStyle (SLAPD/ActiveDirectory)
        """
        Logger.get('auth.ldap').debug('findGroupMemberUids(%s)' % group)
        # In ActiveDirectory users have multivalued attribute 'memberof' with list of groups
        # In SLAPD groups have multivalues attribute 'member' with list of users
        if self.groupStyle == 'ActiveDirectory':
            return self.nestedSearch(self._findDNOfGroup(group), {})
        elif self.groupStyle == 'SLAPD':
            #read member attibute values from the group object
            members = None
            res = self.l.search_s(self._findDNOfGroup(group), ldap.SCOPE_BASE)
            for dn, data in res:
                if dn:
                    members = data['member']
            if not members:
                return []
            memberUids = []
            for memberDN in members:
                memberuid = LDAPTools.extractUIDFromDN(memberDN)
                if memberuid:
                    memberUids.add(memberuid)
            Logger.get('auth.ldap').debug('findGroupMemberUids(%s) returns %s' % (group, memberUids))
            return memberUids
        else:
            raise Exception("Unknown LDAP group style, choices are: SLAPD or ActiveDirectory")

class LDAPGroup(Group):
    groupType = "LDAP"

    def __str__(self):
        return "<LDAPGroup id: %s name: %s desc: %s>" % (self.getId(),
                                                         self.getName(),
                                                         self.getDescription())

    def addMember(self, newMember):
        pass

    def removeMember(self, member):
        pass

    def getMemberList(self):
        uidList = AuthenticatorMgr().getById('LDAP').getGroupMemberList(self.getName())
        avatarLists = []
        for uid in uidList:
            # First, try locally (fast)
            lst = PrincipalHolder().match(uid, exact=1, searchInAuthenticators=False)
            if not lst:
                # If not found, try external
                lst = PrincipalHolder().match(uid, exact=1)
            avatarLists.append(lst)
        return [avList[0] for avList in avatarLists if avList]

    def containsUser(self, avatar):

        # used when checking acces to private events restricted for certain groups
        if not avatar:
            return False
        login = None
        for aid in avatar.getIdentityList():
            if aid.getAuthenticatorTag() == 'LDAP':
                login = aid.getLogin()
        if not login:
            return False
        return AuthenticatorMgr().getById('LDAP').isUserInGroup(login, self.getName())

    def containsMember(self, avatar):
        return 0

class LDAPTools:

    @staticmethod
    def _fromLDAPmultiline(s):
        """
        conversion for inetOrgPerson.postalAddress attribute that can contain
        newlines encoded following the RFC 2252
        """
        if s:
            return s.replace('$', "\r\n").replace('\\24', '$').replace('\\5c', '\\')
        else:
            return s

    @staticmethod
    def extractUserDataFromLdapData(ret):
        """extracts user data from a LDAP record as a dictionary, edit to modify for your needs"""
        udata= {}
        udata["login"] = ret[UID_FIELD]
        udata["email"] = ret['mail']
        udata["name"]= ret.get('givenName', '')
        udata["surName"]= ret.get('sn', '')
        udata["organisation"] = ret.get('company','')
        udata['address'] = LDAPTools._fromLDAPmultiline(ret['postalAddress']) if 'postalAddress' in ret else ''
        udata["phone"] = ret.get('telephoneNumber','')
        udata["fax"] = ret.get('facsimileTelephoneNumber','')
        Logger.get('auth.ldap').debug("extractUserDataFromLdapData(): %s " % udata)
        return udata

    @staticmethod
    def dictToAv(ret):
        """converts user data obtained from LDAP to the structure expected by Avatar"""
        av = {}
        udata=LDAPTools.extractUserDataFromLdapData(ret)
        av["login"] = udata["login"]
        av["email"] = [udata["email"]]
        av["name"]= udata["name"]
        av["surName"]= udata["surName"]
        av["organisation"] = [udata["organisation"]]
        av["address"] = [udata["address"]]
        av["phone"] = udata["phone"]
        av["fax"] = udata["fax"]
        av["id"] = 'LDAP:'+udata["login"]
        av["status"] = "NotCreated"
        return av

    @staticmethod
    def extractUIDFromDN(dn):
        m = re.search('%s=([^,]*),' % UID_FIELD.upper(), dn)
        if m:
            return m.group(1)
        return None
