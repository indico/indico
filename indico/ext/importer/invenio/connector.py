# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Tools to connect to distant Invenio servers using Invenio APIs.


Example of use:

from InvenioConnector import *
cds = InvenioConnector("http://cds.cern.ch")

results = cds.search("higgs")

for record in results:
    print record["245__a"][0]
    print record["520__b"][0]
    for author in record["100__"]:
        print author["a"][0], author["u"][0]

FIXME:
- implement cache expiration
- exceptions handling
- parsing of <!-- Search-Engine-Total-Number-Of-Results: N -->
- better checking of input parameters
- improve behaviour when running locally
    (perform_request_search *requiring* "req" object)
"""

from __future__ import print_function

import urllib
import urllib2
import requests
import xml.sax
import re
import tempfile
import os
import time
import sys

from requests.exceptions import (ConnectionError, InvalidSchema, InvalidURL,
                                 MissingSchema, RequestException)

MECHANIZE_CLIENTFORM_VERSION_CHANGE = (0, 2, 0)
try:
    import mechanize
    if mechanize.__version__ < MECHANIZE_CLIENTFORM_VERSION_CHANGE:
        OLD_MECHANIZE_VERSION = True
        import ClientForm
    else:
        OLD_MECHANIZE_VERSION = False
    MECHANIZE_AVAILABLE = True
except ImportError:
    MECHANIZE_AVAILABLE = False

try:
    # if we are running locally, we can optimize :-)
    from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_SITE_RECORD, CFG_CERN_SITE
    from invenio.legacy.bibsched.bibtask import task_low_level_submission
    from invenio.legacy.search_engine import perform_request_search, collection_restricted_p
    from invenio.modules.formatter import format_records
    from invenio.utils.url import make_user_agent_string
    LOCAL_SITE_URLS = [CFG_SITE_URL, CFG_SITE_SECURE_URL]
    CFG_USER_AGENT = make_user_agent_string("invenio_connector")
except ImportError:
    LOCAL_SITE_URLS = None
    CFG_CERN_SITE = 0
    CFG_USER_AGENT = "invenio_connector"

CFG_CDS_URL = "http://cds.cern.ch/"

class InvenioConnectorAuthError(Exception):
    """
    This exception is called by InvenioConnector when authentication fails during
    remote or local connections.
    """
    def __init__(self, value):
        """
        Set the internal "value" attribute to that of the passed "value" parameter.
        @param value: an error string to display to the user.
        @type value: string
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """
        Return oneself as a string (actually, return the contents of self.value).
        @return: representation of error
        @rtype: string
        """
        return str(self.value)

class InvenioConnectorServerError(Exception):
    """
    This exception is called by InvenioConnector when using it on a machine with no
    Invenio installed and no remote server URL is given during instantiation.
    """
    def __init__(self, value):
        """
        Set the internal "value" attribute to that of the passed "value" parameter.
        @param value: an error string to display to the user.
        @type value: string
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """
        Return oneself as a string (actually, return the contents of self.value).
        @return: representation of error
        @rtype: string
        """
        return str(self.value)

class InvenioConnector(object):
    """
    Creates an connector to a server running Invenio
    """

    def __init__(self, url=None, user="", password="", login_method="Local",
                 local_import_path="invenio", insecure_login=False):
        """
        Initialize a new instance of the server at given URL.

        If the server happens to be running on the local machine, the
        access will be done directly using the Python APIs. In that case
        you can choose from which base path to import the necessary file
        specifying the local_import_path parameter.

        @param url: the url to which this instance will be connected.
            Defaults to CFG_SITE_URL, if available.
        @type url: string
        @param user: the optional username for interacting with the Invenio
            instance in an authenticated way.
        @type user: string
        @param password: the corresponding password.
        @type password: string
        @param login_method: the name of the login method the Invenio instance
            is expecting for this user (in case there is more than one).
        @type login_method: string
        @param local_import_path: the base path from which the connector should
            try to load the local connector, if available. Eg "invenio" will
            lead to "import invenio.dbquery"
        @type local_import_path: string

        @raise InvenioConnectorAuthError: if no secure URL is given for authentication
        @raise InvenioConnectorServerError: if no URL is given on a machine without Invenio installed
        """
        if url == None and LOCAL_SITE_URLS != None:
            self.server_url = LOCAL_SITE_URLS[0] # Default to CFG_SITE_URL
        elif url == None:
            raise InvenioConnectorServerError("You do not seem to have Invenio installed and no remote URL is given")
        else:
            self.server_url = url
        self._validate_server_url()

        self.local = LOCAL_SITE_URLS and self.server_url in LOCAL_SITE_URLS
        self.cached_queries = {}
        self.cached_records = {}
        self.cached_baskets = {}
        self.user = user
        self.password = password
        self.login_method = login_method
        self.browser = None
        if self.user:
            if not insecure_login and not self.server_url.startswith('https://'):
                raise InvenioConnectorAuthError("You have to use a secure URL (HTTPS) to login")
            if MECHANIZE_AVAILABLE:
                self._init_browser()
                self._check_credentials()
            else:
                self.user = None
                raise InvenioConnectorAuthError("The Python module Mechanize (and ClientForm" \
                                                " if Mechanize version < 0.2.0) must" \
                                                " be installed to perform authenticated requests.")

    def _init_browser(self):
        """
        Ovveride this method with the appropriate way to prepare a logged in
        browser.
        """
        self.browser = mechanize.Browser()
        self.browser.set_handle_robots(False)
        self.browser.open(self.server_url + "/youraccount/login")
        self.browser.select_form(nr=0)
        try:
            self.browser['nickname'] = self.user
            self.browser['password'] = self.password
        except:
            self.browser['p_un'] = self.user
            self.browser['p_pw'] = self.password
        # Set login_method to be writable
        self.browser.form.find_control('login_method').readonly = False
        self.browser['login_method'] = self.login_method
        self.browser.submit()

    def _check_credentials(self):
        out = self.browser.response().read()
        if not 'youraccount/logout' in out:
            raise InvenioConnectorAuthError("It was not possible to successfully login with the provided credentials" + out)

    def search(self, read_cache=True, **kwparams):
        """
        Returns records corresponding to the given search query.

        See docstring of invenio.legacy.search_engine.perform_request_search()
        for an overview of available parameters.

        @raise InvenioConnectorAuthError: if authentication fails
        """
        parse_results = False
        of = kwparams.get('of', "")
        if of == "":
            parse_results = True
            of = "xm"
            kwparams['of'] = of
        params = urllib.urlencode(kwparams, doseq=1)

        # Are we running locally? If so, better directly access the
        # search engine directly
        if self.local and of != 't':
            # See if user tries to search any restricted collection
            c = kwparams.get('c', "")
            if c != "":
                if type(c) is list:
                    colls = c
                else:
                    colls = [c]
                for collection in colls:
                    if collection_restricted_p(collection):
                        if self.user:
                            self._check_credentials()
                            continue
                        raise InvenioConnectorAuthError("You are trying to search a restricted collection. Please authenticate yourself.\n")
            kwparams['of'] = 'id'
            results = perform_request_search(**kwparams)
            if of.lower() != 'id':
                results = format_records(results, of)
        else:
            if params + str(parse_results) not in self.cached_queries or not read_cache:
                if self.user:
                    results = self.browser.open(self.server_url + "/search?" + params)
                else:
                    results = urllib2.urlopen(self.server_url + "/search?" + params)
                if 'youraccount/login' in results.geturl():
                    # Current user not able to search collection
                    raise InvenioConnectorAuthError("You are trying to search a restricted collection. Please authenticate yourself.\n")
            else:
                return self.cached_queries[params + str(parse_results)]

        if parse_results:
            # FIXME: we should not try to parse if results is string
            parsed_records = self._parse_results(results, self.cached_records)
            self.cached_queries[params + str(parse_results)] = parsed_records
            return parsed_records
        else:
            # pylint: disable=E1103
            # The whole point of the following code is to make sure we can
            # handle two types of variable.
            try:
                res = results.read()
            except AttributeError:
                res = results
            # pylint: enable=E1103

            if of == "id":
                try:
                    if type(res) is str:
                        # Transform to list
                        res = [int(recid.strip()) for recid in \
                        res.strip("[]").split(",") if recid.strip() != ""]
                    res.reverse()
                except (ValueError, AttributeError):
                    res = []
            self.cached_queries[params + str(parse_results)] = res
            return self.cached_queries[params + str(parse_results)]

    def search_with_retry(self, sleeptime=3.0, retrycount=3, **params):
        """
        This function performs a search given a dictionary of search(..)
        parameters. It accounts for server timeouts as necessary and
        will retry some number of times.

        @param sleeptime: number of seconds to sleep between retries
        @type sleeptime: float

        @param retrycount: number of times to retry given search
        @type retrycount: int

        @param params: search parameters
        @type params: **kwds

        @rtype: list
        @return: returns records in given format
        """
        results = []
        count = 0
        while count < retrycount:
            try:
                results = self.search(**params)
                break
            except urllib2.URLError:
                sys.stderr.write("Timeout while searching...Retrying\n")
                time.sleep(sleeptime)
                count += 1
        else:
            sys.stderr.write("Aborting search after %d attempts.\n" % (retrycount,))
        return results

    def search_similar_records(self, recid):
        """
        Returns the records similar to the given one
        """
        return self.search(p="recid:" + str(recid), rm="wrd")

    def search_records_cited_by(self, recid):
        """
        Returns records cited by the given one
        """
        return self.search(p="recid:" + str(recid), rm="citation")

    def get_records_from_basket(self, bskid, group_basket=False, read_cache=True):
        """
        Returns the records from the (public) basket with given bskid
        """
        if bskid not in self.cached_baskets or not read_cache:
            if self.user:
                if group_basket:
                    group_basket = '&category=G'
                else:
                    group_basket = ''
                results = self.browser.open(self.server_url + \
                        "/yourbaskets/display?of=xm&bskid=" + str(bskid) + group_basket)
            else:
                results = urllib2.urlopen(self.server_url + \
                        "/yourbaskets/display_public?of=xm&bskid=" + str(bskid))
        else:
            return self.cached_baskets[bskid]

        parsed_records = self._parse_results(results, self.cached_records)
        self.cached_baskets[bskid] = parsed_records
        return parsed_records

    def get_record(self, recid, read_cache=True):
        """
        Returns the record with given recid
        """
        if recid in self.cached_records or not read_cache:
            return self.cached_records[recid]
        else:
            return self.search(p="recid:" + str(recid))

    def upload_marcxml(self, marcxml, mode):
        """
        Uploads a record to the server

        Parameters:
          marcxml - *str* the XML to upload.
             mode - *str* the mode to use for the upload.
                    "-i" insert new records
                    "-r" replace existing records
                    "-c" correct fields of records
                    "-a" append fields to records
                    "-ir" insert record or replace if it exists
        """
        if mode not in ["-i", "-r", "-c", "-a", "-ir"]:
            raise NameError, "Incorrect mode " + str(mode)

        # Are we running locally? If so, submit directly
        if self.local:
            (code, marcxml_filepath) = tempfile.mkstemp(prefix="upload_%s" % \
                                                        time.strftime("%Y%m%d_%H%M%S_",
                                                                      time.localtime()))
            marcxml_file_d = os.fdopen(code, "w")
            marcxml_file_d.write(marcxml)
            marcxml_file_d.close()
            return task_low_level_submission("bibupload", "", mode, marcxml_filepath)
        else:
            params = urllib.urlencode({'file': marcxml,
                                        'mode': mode})
            ## We don't use self.browser as batchuploader is protected by IP
            opener = urllib2.build_opener()
            opener.addheaders = [('User-Agent', CFG_USER_AGENT)]
            return opener.open(self.server_url + "/batchuploader/robotupload", params,)

    def _parse_results(self, results, cached_records):
        """
        Parses the given results (in MARCXML format).

        The given "cached_records" list is a pool of
        already existing parsed records (in order to
        avoid keeping several times the same records in memory)
        """
        parser = xml.sax.make_parser()
        handler = RecordsHandler(cached_records)
        parser.setContentHandler(handler)
        parser.parse(results)
        return handler.records

    def _validate_server_url(self):
        """Validates self.server_url"""
        try:
            request = requests.head(self.server_url)
            if request.status_code >= 400:
                raise InvenioConnectorServerError(
                    "Unexpected status code '%d' accessing URL: %s"
                    % (request.status_code, self.server_url))
        except (InvalidSchema, MissingSchema) as err:
            raise InvenioConnectorServerError(
                "Bad schema, expecting http:// or https://:\n %s" % (err,))
        except ConnectionError as err:
            raise InvenioConnectorServerError(
                "Couldn't establish connection to '%s':\n %s"
                % (self.server_url, err))
        except InvalidURL as err:
            raise InvenioConnectorServerError(
                "Invalid URL '%s':\n %s"
                % (self.server_url, err))
        except RequestException as err:
            raise InvenioConnectorServerError(
                "Unknown error connecting to '%s':\n %s"
                % (self.server_url, err))


class Record(dict):
    """
    Represents a Invenio record
    """
    def __init__(self, recid=None, marcxml=None, server_url=None):
        #dict.__init__(self)
        self.recid = recid
        self.marcxml = ""
        if marcxml is not None:
            self.marcxml = marcxml
        #self.record = {}
        self.server_url = server_url

    def __setitem__(self, item, value):
        tag, ind1, ind2, subcode = decompose_code(item)
        if subcode is not None:
            #if not dict.has_key(self, tag + ind1 + ind2):
            #   dict.__setitem__(self, tag + ind1 + ind2, [])
            dict.__setitem__(self, tag + ind1 + ind2, [{subcode: [value]}])
        else:
            dict.__setitem__(self, tag + ind1 + ind2, value)

    def __getitem__(self, item):
        tag, ind1, ind2, subcode = decompose_code(item)

        datafields = dict.__getitem__(self, tag + ind1 + ind2)
        if subcode is not None:
            subfields = []
            for datafield in datafields:
                if subcode in datafield:
                    subfields.extend(datafield[subcode])
            return subfields
        else:
            return datafields

    def __contains__(self, item):
        return dict.__contains__(item)

    def __repr__(self):
        return "Record(" + dict.__repr__(self) + ")"

    def __str__(self):
        return self.marcxml

    def export(self, of="marcxml"):
        """
        Returns the record in chosen format
        """
        return self.marcxml

    def url(self):
        """
        Returns the URL to this record.
        Returns None if not known
        """
        if self.server_url is not None and \
            self.recid is not None:
            return self.server_url + "/"+ CFG_SITE_RECORD +"/" + str(self.recid)
        else:
            return None
if MECHANIZE_AVAILABLE:
    class _SGMLParserFactory(mechanize.DefaultFactory):
        """
        Black magic to be able to interact with CERN SSO forms.
        """
        def __init__(self, i_want_broken_xhtml_support=False):
            if OLD_MECHANIZE_VERSION:
                forms_factory = mechanize.FormsFactory(
                    form_parser_class=ClientForm.XHTMLCompatibleFormParser)
            else:
                forms_factory = mechanize.FormsFactory(
                    form_parser_class=mechanize.XHTMLCompatibleFormParser)
            mechanize.Factory.__init__(
                self,
                forms_factory=forms_factory,
                links_factory=mechanize.LinksFactory(),
                title_factory=mechanize.TitleFactory(),
                response_type_finder=mechanize._html.ResponseTypeFinder(
                    allow_xhtml=i_want_broken_xhtml_support),
                )

    class CDSInvenioConnector(InvenioConnector):
        def __init__(self, user="", password="", local_import_path="invenio"):
            """
            This is a specialized InvenioConnector class suitable to connect
            to the CERN Document Server (CDS), which uses centralized SSO.
            """
            cds_url = CFG_CDS_URL
            if user:
                cds_url = cds_url.replace('http', 'https')
            super(CDSInvenioConnector, self).__init__(cds_url, user, password, local_import_path=local_import_path)

        def _init_browser(self):
            """
            @note: update this everytime the CERN SSO login form is refactored.
            """
            self.browser = mechanize.Browser(factory=_SGMLParserFactory(i_want_broken_xhtml_support=True))
            self.browser.set_handle_robots(False)
            self.browser.open(self.server_url)
            self.browser.follow_link(text_regex="Sign in")
            self.browser.select_form(nr=0)
            self.browser.form['ctl00$ctl00$NICEMasterPageBodyContent$SiteContentPlaceholder$txtFormsLogin'] = self.user
            self.browser.form['ctl00$ctl00$NICEMasterPageBodyContent$SiteContentPlaceholder$txtFormsPassword'] = self.password
            self.browser.submit()
            self.browser.select_form(nr=0)
            self.browser.submit()

class RecordsHandler(xml.sax.handler.ContentHandler):
    "MARCXML Parser"

    def __init__(self, records):
        """
        Parameters:
           records  -  *dict* a dictionary with an already existing cache of records
        """
        self.cached_records = records
        self.records = []
        self.in_record = False
        self.in_controlfield = False
        self.in_datafield = False
        self.in_subfield = False
        self.cur_tag = None
        self.cur_subfield = None
        self.cur_controlfield = None
        self.cur_datafield = None
        self.cur_record = None
        self.recid = 0
        self.buffer = ""
        self.counts = 0

    def startElement(self, name, attributes):
        if name == "record":
            self.cur_record = Record()
            self.in_record = True

        elif name == "controlfield":
            tag = attributes["tag"]
            self.cur_datafield = ""
            self.cur_tag = tag
            self.cur_controlfield = []
            if tag not in self.cur_record:
                self.cur_record[tag] = self.cur_controlfield
            self.in_controlfield = True

        elif name == "datafield":
            tag = attributes["tag"]
            self.cur_tag = tag
            ind1 = attributes["ind1"]
            if ind1 == " ": ind1 = "_"
            ind2 = attributes["ind2"]
            if ind2 == " ": ind2 = "_"
            if tag + ind1 + ind2 not in self.cur_record:
                self.cur_record[tag + ind1 + ind2] = []
            self.cur_datafield = {}
            self.cur_record[tag + ind1 + ind2].append(self.cur_datafield)
            self.in_datafield = True

        elif name == "subfield":
            subcode = attributes["code"]
            if subcode not in self.cur_datafield:
                self.cur_subfield = []
                self.cur_datafield[subcode] = self.cur_subfield
            else:
                self.cur_subfield = self.cur_datafield[subcode]
            self.in_subfield = True

    def characters(self, data):
        if self.in_subfield:
            self.buffer += data
        elif self.in_controlfield:
            self.buffer += data
        elif "Search-Engine-Total-Number-Of-Results:" in data:
            print(data)
            match_obj = re.search("\d+", data)
            if match_obj:
                print(int(match_obj.group()))
                self.counts = int(match_obj.group())

    def endElement(self, name):
        if name == "record":
            self.in_record = False
        elif name == "controlfield":
            if self.cur_tag == "001":
                self.recid = int(self.buffer)
                if self.recid in self.cached_records:
                    # Record has already been parsed, no need to add
                    pass
                else:
                    # Add record to the global cache
                    self.cached_records[self.recid] = self.cur_record
                # Add record to the ordered list of results
                self.records.append(self.cached_records[self.recid])

            self.cur_controlfield.append(self.buffer)
            self.in_controlfield = False
            self.buffer = ""
        elif name == "datafield":
            self.in_datafield = False
        elif name == "subfield":
            self.in_subfield = False
            self.cur_subfield.append(self.buffer)
            self.buffer = ""


def decompose_code(code):
    """
    Decomposes a MARC "code" into tag, ind1, ind2, subcode
    """
    code = "%-6s" % code
    ind1 = code[3:4]
    if ind1 == " ": ind1 = "_"
    ind2 = code[4:5]
    if ind2 == " ": ind2 = "_"
    subcode = code[5:6]
    if subcode == " ": subcode = None
    return (code[0:3], ind1, ind2, subcode)
