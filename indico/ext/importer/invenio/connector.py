# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio;if not, see <http://www.gnu.org/licenses/>.
"""
Tools to connect to distant Invenio servers using Invenio APIs.

Example of use:

from InvenioConnector import *
cds = InvenioConnector("http://cdsweb.cern.ch")

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
- better checking of input parameters (especially InvenioConnector.__init__ "url")
- improve behaviour when running locally (perform_request_search *requiring* "req" object)
"""
import urllib
import urllib2
import xml.sax
import re
import tempfile
import os
import time
from email import mime, Encoders
import StringIO
try:
    # if we are running locally, we can optimize :-)
    from invenio.config import CFG_SITE_URL
    from invenio.bibtask import task_low_level_submission
    from invenio.search_engine import perform_request_search
    from invenio.bibformat import format_records
    LOCAL_SITE_URL = CFG_SITE_URL
except ImportError:
    LOCAL_SITE_URL = None

class InvenioConnector:
    """
    Creates an connector to a server running Invenio
    """

    def __init__(self, url, local_import_path="invenio",
                 user_agent="invenio_connector"):
        """
        Initialize a new instance of the server at given URL.

        If the server happens to be running on the local machine, the
        access will be done directly using the Python APIs. In that case
        you can choose from which base path to import the necessary file
        specifying the local_import_path parameter.

        Parameters:
                       url - *str* the url to which this instance will
                             be connected

         local_import_path - *str* the base path from which the
                             connector should try to load the local
                             connector, if available. Eg "invenio"
                             will lead to "import invenio.dbquery"
         """
        self.server_url = url
        self.user_agent = user_agent
        self.cached_queries = {}
        self.cached_records = {}
        self.cached_baskets = {}

    def search(self, p="", f="", c="", rg=10, sf="", so="d", sp="",
               rm="", of="", ot="", p1="", f1="", m1="", op1="",
               p2="", f2="", m2="", op2="", p3="", f3="", m3="",
               jrec=0, recid=-1, recidb=-1, d1="", d1y=0, d1m=0,
               d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", ap=0,
               read_cache=True):
        """
        Returns records corresponding to the given search query.
        """
        parse_results = False
        if of == "":
            parse_results = True
            of = "xm"

        params = {'p': p, 'f': f, 'c': c, 'rg': rg,
                  'sf': sf, 'so': so, 'sp': sp,
                  'rm': rm, 'of': of,
                  'p1':p1, 'f1': f1, 'm1': m1, 'op1': op1,
                  'p2': p2, 'f2': f2, 'm2': m2, 'op2': op2,
                  'p3': p3, 'f3': f3, 'm3': m3, 'jrec':jrec,
                  'd1': d1, 'd1y':d1y, 'd1m': d1m, 'd1d': d1d,
                  'd2': d2, 'd2y': d2y, 'd2m': d2m, 'd2d': d2d,
                  'dt': dt, 'ap': ap , 'recid': recid, 'recidb': recidb,
                   'ot': ot}
        if recid == -1:
            del params['recid']
        if recidb == -1:
            del params['recidb']
        params = urllib.urlencode(params)

        # Are we running locally? If so, better directly access the
        # search engine directly
        if LOCAL_SITE_URL == self.server_url and \
               of != 't':
            results = perform_request_search(p=p, f=f, c=c, rg=rg, sf=sf, so=so, sp=so, rm=rm,
                                            p1=p1, f1=f1, m1=m1, op1=op1,
                                            p2=p2, f2=f2, m2=m2, op2=op2,
                                            p3=p3, f3=f3, m3=m3, jrec=jrec,
                                            recid=recid, recidb=recidb, of='id', ot=ot,
                                            d1=d1, d1y=d1y, d1m=d1m, d1d=d1d,
                                            d2=d2, d2y=d2y, d2m=d2m, d2d=d2d, dt=dt, ap=ap)
            if of.lower() != 'id':
                results = format_records(results, of)
        else:
            if not self.cached_queries.has_key(params + str(parse_results)) or not read_cache:
                results = urllib2.urlopen(self.server_url + "/search?" + params)
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
                if type(res) is str:
                    # Transform to list
                    res = [int(recid.strip()) for recid in \
                    res.strip("[]").split(",") if recid.strip() != ""]
                res.reverse()
            self.cached_queries[params + str(parse_results)] = res
            return self.cached_queries[params + str(parse_results)]

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

    def get_records_from_basket(self, bskid, read_cache=True):
        """
        Returns the records from the (public) basket with given bskid
        """
        if not self.cached_baskets.has_key(bskid) or not read_cache:
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
        if self.cached_records.has_key(recid) or not read_cache:
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
        if LOCAL_SITE_URL == self.server_url:
            (code, marcxml_filepath) = tempfile.mkstemp(prefix="upload_%s" % \
                                                        time.strftime("%Y%m%d_%H%M%S_",
                                                                      time.localtime()))
            marcxml_file_d = os.fdopen(code, "w")
            marcxml_file_d.write(marcxml)
            marcxml_file_d.close()
            return task_low_level_submission("bibupload", "", mode, marcxml_filepath)
        else:
            # add parameters
            tpart = mime.Text.MIMEText(mode)
            tpart.add_header("Content-Disposition", "form-data", name='mode')

            # add file
            fpart = mime.Base.MIMEBase('application', "octet-stream")
            fpart.set_payload(marcxml)
            fpart.add_header('Content-Disposition',
                             'form-data; name="file"; filename="marcxml_upload.xml"')

            #Encoders.encode_base64(fpart)

            BOUNDARY = '------------------------------6510e6bc42e6'

            data = BOUNDARY + '\n' + fpart.as_string() + '\n' + \
                   BOUNDARY + '\n' + tpart.as_string() + '\n' + BOUNDARY + '--\n'

            data = data.replace('\n', '\r\n')

            req = urllib2.Request(self.server_url + "/batchuploader/robotupload",
                                  data,
                                  {'User-Agent': self.user_agent,
                                   'Content-Type': 'multipart/form-data; boundary=%s' %
                                   BOUNDARY[2:]})
            return urllib2.urlopen(req)

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
                if datafield.has_key(subcode):
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
            return self.server_url + "/record/" + str(self.recid)
        else:
            return None

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
            if not self.cur_record.has_key(tag):
                self.cur_record[tag] = self.cur_controlfield
            self.in_controlfield = True

        elif name == "datafield":
            tag = attributes["tag"]
            self.cur_tag = tag
            ind1 = attributes["ind1"]
            if ind1 == " ": ind1 = "_"
            ind2 = attributes["ind2"]
            if ind2 == " ": ind2 = "_"
            if not self.cur_record.has_key(tag + ind1 + ind2):
                self.cur_record[tag + ind1 + ind2] = []
            self.cur_datafield = {}
            self.cur_record[tag + ind1 + ind2].append(self.cur_datafield)
            self.in_datafield = True

        elif name == "subfield":
            subcode = attributes["code"]
            if not self.cur_datafield.has_key(subcode):
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
            print data
            match_obj = re.search("\d+", data)
            if match_obj:
                print int(match_obj.group())
                self.counts = int(match_obj.group())

    def endElement(self, name):
        if name == "record":
            self.in_record = False
        elif name == "controlfield":
            if self.cur_tag == "001":
                self.recid = int(self.buffer)
                if self.cached_records.has_key(self.recid):
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
