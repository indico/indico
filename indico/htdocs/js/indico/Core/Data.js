/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

// Place where to put page-wide Indico-related global variables
var IndicoGlobalVars = {};

var Util = {
    parseId: function(id){

        /* Returns the type and the split ids for a provided composite id */

        // [1234.]s0
        var m = id.match(/^(?:([^\.]+)\.)?s(\d+)$/);
        if (m) {
            return concat(["Session"], m.slice(1));
        }

        // [1234.]s0.0
        m = id.match(/^(?:([^\.]+)\.)s(\d+)(?:\.|l)(\d+)$/);
        if (m) {
            return concat(["SessionSlot"], m.slice(1));
        }

        // [1234.]33
        m = id.match(/^(?:([^\.]+)\.)(\d+)$/);
        if (m) {
            return concat(["Contribution"], m.slice(1));
        }

        // otherwise, consider it is a conference
        return concat(["Conference"], [id]);
    },

    //truncate titles which are too long
    truncate: function(title, length){
        length = length || 25;
        if(title.length > length){
            return title.substring(0,length-3) + "...";
        }else{
            return title;
        }
    },

    /* formats a datetime dictionary, Date object
       or string date (different format) as a string,
       considering formats (sourceFormat used for strings only) */
    formatDateTime: function(obj, format, sourceFormat){
        // default value
        format = format || "%d/%m/%Y %H:%M";

        var m1 = null, m2 = null;

        if (obj === null) {
            return null;
        }
        // handle date object
        else if (obj.constructor == Date) {
            m1 = [null, obj.getFullYear(), obj.getMonth()+1, obj.getDate()];
            m2 = [null, zeropad(obj.getHours()), obj.getMinutes(), obj.getSeconds()];
        } else if (typeof(obj) == 'object'){
            // handle datetime dictionaries
            // data comes from the server in %Y-%m-%d %H:%M:%S
            m1 = obj.date.match(/(\d+)[\-\/](\d+)[\-\/](\d+)/);
            m2 = obj.time.match(/(\d+):(\d+)(?:\:(\d+))?/);
        } else if (sourceFormat){
            // handle strings

            // parse first
            var results = Util.__parseDateTime(obj, sourceFormat);

            // map the results
            m1 = [null, results['%Y'], results['%m'], results['%d']];
            //If we do not want to show the hour
            m2 = [null, any(results['%H'],''), any(results['%M'],''), any(results['%S'],'')];
        } else {
            throw 'unknown source object';
        }

        if (!m1 || !m2) {
            return null;
        }

        return format.replace('%Y', zeropad(m1[1])).
        replace('%m', zeropad(m1[2])).
        replace('%d', zeropad(m1[3])).
        replace('%H', zeropad(m2[1])).
        replace('%M', zeropad(m2[2])).
        replace('%S', zeropad(m2[3]));
    },

    /*
     * Internal use only!
     * Does basic date/time parsing
     */
    __parseDateTime: function(string, format) {
        // default value
        format = format || "%Y/%m/%d %H:%M";

        if (!string) {
            return null;
        }

        var tokenOrder = [];

        // build a regular expression from the format spec
        var reFormat = format.replace(/%\w/g,function(val) {
            // add the tokens in order to the list
            tokenOrder.push(val);
            return val=='%Y'?'(\\d{0,4})':'(\\d{0,2})';
        }).
        replace(' ','\\s+');

        // apply the regexp
        var m = string.match('^'+reFormat+'$');

        if (!m) {
            // if there are no matches, stop
            return null;
        }

        // set seconds at zero (sometimes they're not specified)
        var results = {'%Y': 0, '%m': 1, '%d': 1, '%H': 0, '%M': 0, '%S': 0};

        // store the results, relative to the token order
        for (var i = 1; i < m.length; ++i) {
            results[tokenOrder[i-1]] = m[i];
        }

        return results;
    },

    /* parses a string into a JavaScript Date object,
       considering formats */
    parseJSDateTime: function(string, format) {

        var results = Util.__parseDateTime(string, format);

        if(!results) {
            return null;
        }

        var date = new Date(results['%Y'], results['%m']-1, results['%d']);

        if (date.getDate() != results['%d'] || (date.getMonth() + 1) != results['%m']) {
            // stuff such as 31/11
            return null
        }

        setTime(date, [results['%H'], results['%M'], results['%S']]);

        return date;
    },

    /* parses a string into a datetime dictionary,
       considering formats */
    parseDateTime: function(string, format){

        var results = Util.__parseDateTime(string, format);

        if(!results) {
            return null;
        }

        // build the actual dates in standard format (zeropad too)
        return {date: zeropad(results['%Y'])+'/'+zeropad(results['%m'])+'/'+zeropad(results['%d']),
                time: zeropad(results['%H'])+':'+zeropad(results['%M'])+':'+zeropad(results['%S'])};
    },

    dateTimeIndicoToJS: function(obj) {
        var m1 = obj.date.match(/(\d+)[\-\/](\d+)[\-\/](\d+)/);
        var m2 = obj.time.match(/(\d+):(\d+)(?::(\d+))?/);


        var date = new Date(m1[1],m1[2] - 1,m1[3]||0);
        setTime(date, [m2[1],m2[2],m2[3]]);

        return date;
    },

    HTMLEscape: function(text) {
        // escape special HTML chars - kind of hacky but works
        return $('<p/>').text(text || '').html();
    }

};

Util.Validation = {
    isEmailAddress: function(address) {
        // Adapted RFC2822 (thanks to Jan Goyvaerts)
        return exists(address.toLowerCase().match(/^[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+(?:\.[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+)*@(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?$/));
    },

    isURL: function(address) {
        // per RFC2396, but forcing xxx: prefix and at least some text after
        return exists(address.match(/^(([^:\/?#]+):)((\/\/)?([^\/?#]+))([^?#]*)(\?([^#]*))?(#(.*))?$/));
    },

    isHtml: function(text) {
        return /<.*>[\s\S]*<\/.*>|<br\s*\/>/.exec(text);
    }
};


var IndicoDateTimeFormats = {
    International: '%d/%m/%Y %H:%M',
    ISO8601: '%Y/%m/%d %H:%M',
    Ordinal: '%Y%m%d'
};

IndicoDateTimeFormats.Default = IndicoDateTimeFormats.International;
IndicoDateTimeFormats.Server = IndicoDateTimeFormats.ISO8601;

IndicoDateTimeFormats.DefaultHourless = IndicoDateTimeFormats.Default.split(' ')[0];
IndicoDateTimeFormats.ServerHourless = IndicoDateTimeFormats.Server.split(' ')[0];
