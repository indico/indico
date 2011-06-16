# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


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

and groups listing their members by DNs, like:

dn: cn=somegroup,ou=groups,dc=example,dc=com
objectClass: groupOfNames
cn: somegroup
member: uid=john,ou=people,dc=example,dc=com
member: uid=alice,ou=people,dc=example,dc=com
member: uid=bob,ou=people,dc=example,dc=com
description: Just a group of people ...

Adjust it to your needs if your LDAP structure is different.

See indico.conf for information about customization options.
"""

# python-ldap
try:
    import ldap
    import ldap.filter
except:
    pass

# legacy indico imports
from MaKaC.authentication.baseAuthentication import Authenthicator, PIdentity
from MaKaC.errors import MaKaCError
from MaKaC.common.logger import Logger
from MaKaC.common import Configuration


RETRIEVED_FIELDS = ['uid', 'cn', 'mail', 'o', 'ou', 'company', 'givenName',
                    'sn', 'postalAddress', 'userPrincipalName']


class LDAPAuthenticator(Authenthicator):
    idxName = "LDAPIdentities"
    id = 'LDAP'
    name = 'LDAP'
    description = "LDAP Login"

    def __init__(self):
        Authenthicator.__init__(self)
        self.UserCreator = LDAPUserCreator()

    def createIdentity(self, li, avatar):
        Logger.get("auth.ldap").info("createIdentity %s (%s %s)" % \
                                     (li.getLogin(), avatar.getId(),
                                      avatar.getEmail()))
        if LDAPChecker().check(li.getLogin(), li.getPassword()):
            return LDAPIdentity(li.getLogin(), avatar)
        else:
            return None


class LDAPIdentity(PIdentity):

    def __str__(self):
        return '<LDAPIdentity{login:%s, tag:%s}>' % \
               (self.getLogin(), self.getAuthenticatorTag())

    def authenticate(self, id):
        """
        id is MaKaC.user.LoginInfo instance, self.user is Avatar
        """

        Logger.get('auth.ldap').info("authenticate(%s)" % id.getLogin())
        data = LDAPChecker().check(id.getLogin(), id.getPassword())
        if data:
            if self.getLogin() == id.getLogin():
                # modify Avatar with the up-to-date info from LDAP
                av = self.user

                if 'postalAddress' in data:
                    postalAddress = fromLDAPmultiline(data['postalAddress'])
                    if av.getAddress() != postalAddress:
                        av.setAddress(postalAddress)

                if 'sn' in data:
                    surname = data['sn']
                    if av.getSurName() != surname:
                        av.setSurName(surname)

                if 'givenName' in data:
                    firstName = data['givenName']
                    if av.getName() != firstName:
                        av.setName(firstName)

                if 'o' in data:
                    org = data.get('o', '')
                else:
                    org = data.get('company', '')

                if org.strip() != '' and org != av.getOrganisation():
                    av.setOrganisation(org)

                mail = data.get('mail', '')

                if mail.strip() != '' and mail != av.getEmail():
                    av.setEmail(mail)

                return self.user
            else:
                return None
        return None

    def getAuthenticatorTag(self):
        return LDAPAuthenticator.getId()


def objectAttributes(dn, result_data, attributeNames):
    """
    adds selected attributes
    """
    object = {'dn': dn}
    for name in attributeNames:
        addAttribute(object, result_data, name)
    return object


def addAttribute(object, attrMap, attrName):
    """
    safely adds attribute
    """
    if attrName in attrMap:
        attr = attrMap[attrName]
        if len(attr) == 1:
            object[attrName] = attr[0]
        else:
            object[attrName] = attr


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
        ldapConfig = conf.getLDAPConfig()
        self.ldapHost = ldapConfig.get('host')
        self.ldapPeopleFilter, self.ldapPeopleDN = \
                               ldapConfig.get('peopleDNQuery')
        self.ldapGroupsFilter, self.ldapGroupsDN = \
                               ldapConfig.get('groupDNQuery')
        self.ldapAccessCredentials = ldapConfig.get('accessCredentials')
        self.ldapMembershipQuery = ldapConfig.get('membershipQuery')
        self.ldapUseTLS = ldapConfig.get('useTLS')

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
        self.l = ldap.open(self.ldapHost)
        self.l.protocol_version = ldap.VERSION3

        if self.ldapUseTLS:
            self.l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
        else:
            self.l.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_NEVER)

        if self.ldapUseTLS:
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
                return objectAttributes(dn, data, RETRIEVED_FIELDS)
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
                ret = objectAttributes(dn, data, RETRIEVED_FIELDS)
                av = dictToAv(ret)
                d[ret['mail']] = av
        return d

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
        res = self.l.search_s(self.ldapGroupsDN, ldap.SCOPE_SUBTREE, gfilter)
        groupDicts = []
        for dn, data in res:
            if dn:
                groupDicts.append(objectAttributes(
                    dn, data, ['cn', 'description']))
        return groupDicts

    def userInGroup(self, login, name):
        """
        Finds uids of users referenced by the member attribute
        of the group LDAP object
        """
        query = self.ldapMembershipQuery.format(self._findDNOfGroup(name))
        res = self.l.search_s(self._findDNOfUser(login), ldap.SCOPE_BASE, query)

        return res != []


class LDAPChecker(object):
    def check(self, userName, password):
        try:
            ret = {}
            ldapc = LDAPConnector()
            ldapc.openAsUser(userName, password)
            ret = ldapc.lookupUser(userName)
            ldapc.close()
            Logger.get('auth.ldap').debug("Username: %s checked: %s" % \
                                          (userName, ret))
            return ret
        except ldap.INVALID_CREDENTIALS:
            Logger.get('auth.ldap').exception(
                "Username: %s - invalid credentials" % userName)
            return None


def fromLDAPmultiline(s):
    """
    conversion for inetOrgPerson.postalAddress attribute that can contain
    newlines encoded following the RFC 2252
    """
    if s:
        return s.replace('$', "\r\n").replace('\\24', '$').replace('\\5c', '\\')
    else:
        return s


class LDAPUserCreator(object):

    def create(self, li):
        Logger.get('auth.ldap').info("create '%s'" % li.getLogin())
        # first, check if authentication is OK
        data = LDAPChecker().check(li.getLogin(), li.getPassword())
        if not data:
            return None

        # Search if user already exist, using email address
        import MaKaC.user as user
        ah = user.AvatarHolder()
        userList = ah.match({"email": data["mail"]}, forceWithoutExtAuth=True)
        if len(userList) == 0:
            # User doesn't exist, create it
            try:
                av = user.Avatar()
                name = data.get('cn')
                av.setName(name.split()[0])
                av.setSurName(name.split()[-1])
                av.setOrganisation(data.get('o', ""))
                av.setEmail(data['mail'])
                if 'postalAddress' in data:
                    av.setAddress(fromLDAPmultiline(data.get('postalAddress')))
                #av.setTelephone(data.get('telephonenumber',""))
                ah.add(av)
                av.activateAccount()
            except KeyError:
                raise MaKaCError("LDAP account does not contain the mandatory"
                                 "data to create an Indico account.")
        else:
            # user founded
            av = userList[0]
        #now create the nice identity for the user
        na = LDAPAuthenticator()
        id = na.createIdentity(li, av)
        na.add(id)
        return av


# for MaKaC.externUsers
def dictToAv(ret):
    av = {}
    av["email"] = [ret['mail']]
    av["name"] = ret.get('givenName', '')
    av["surName"] = ret.get('sn', '')

    if 'o' in ret:
        av["organisation"] = [ret.get('o', '')]
    else:
        av["organisation"] = [ret.get('company', '')]

    if 'postalAddress' in ret:
        av['address'] = [fromLDAPmultiline(ret['postalAddress'])]

    av["login"] = ret.get('uid') if 'uid' in ret else ret['userPrincipalName']
    av["id"] = 'LDAP:' + av["login"]
    av["status"] = "NotCreated"
    return av


def is_empty(dict, key):
    if key not in dict:
        return False
    if dict[key]:
        return True
    else:
        return False


class LDAPUser(object):

    _operations = {
        'email': '(mail={0})',
        'name': '(givenName={0})',
        'surName': '(sn={0})',
        'organisation': '(|(o={0})(ou={0}))',
        'login': '(uid={0})'
        }

    def match(self, criteria, exact=0):
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

    def getById(self, id):
        ldapc = LDAPConnector()
        ldapc.open()
        ldapc.login()
        ret = ldapc.lookupUser(id)
        ldapc.close()
        if(ret == None):
            return None
        av = dictToAv(ret)
        av["id"] = id
        av["identity"] = LDAPIdentity
        av["authenticator"] = LDAPAuthenticator()
        return av


def ldapFindGroups(name, exact):
    ldapc = LDAPConnector()
    ldapc.open()
    ldapc.login()
    ret = ldapc.findGroups(ldap.filter.escape_filter_chars(name), exact)
    ldapc.close()
    return ret


def ldapUserInGroup(user, name):
    ldapc = LDAPConnector()
    ldapc.open()
    ldapc.login()
    ret = ldapc.userInGroup(user, name)
    ldapc.close()
    return ret
