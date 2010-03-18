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
        var results = {'%S': 0};

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

        var date = new Date();

        setDate(date, [results['%d'],results['%m'],results['%Y']]);
        setTime(date, [results['%H'],results['%M'],results['%S']]);

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
        m1 = obj.date.match(/(\d+)[\-\/](\d+)[\-\/](\d+)/);
        m2 = obj.time.match(/(\d+):(\d+):(\d+)/);

        var date = new Date();

        setDate(date, [m1[3],m1[2],m1[1]]);
        setTime(date, [m2[1],m2[2],m2[3]]);

        return date;
    },

    dateTimeJSToIndico: function(obj){
        return {date:  obj.getFullYear()+ '/'+ zeropad(obj.getMonth()+1) + '/' + zeropad(obj.getDate()),
                time: zeropad(obj.getHours())+':'+zeropad(obj.getMinutes())+':'+zeropad(obj.getSeconds())};
    }

};

Util.Validation = {
    isIPAddress: function(address) {
        // thanks to Jan Goyvaerts
        return exists(address.match(/^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/));
    },

    isEmailAddress: function(address) {
        // Adapted RFC2822 (thanks to Jan Goyvaerts)
        return exists(address.toLowerCase().match(/^[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+(?:\.[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+)*@(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?$/));
    },

    isEmailList: function(emails) {
        // check if the emails given are valid and if valid separators are used
        return exists(emails.toLowerCase().match(/^(?:[ ,;]*)(?:[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+(?:\.[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+)*@(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?)(?:[ ,;]+(?:[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+(?:\.[a-z0-9!#$%&\'*+\/=?\^_`{|}~\-]+)*@(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?))*(?:[ ,;]*)$/));
    },
    isURL: function(address) {
        // thanks to Jan Goyvaerts
        return exists(address.match(/^http\:\/\/(.+)$/));
    }


};

Protection = {

    ParentRestrictionMessages: {
        '1': $T("(currently <strong>restricted</strong> to some users, but can change)"),
        '-1': $T("(currently <strong>open</strong> to everyone, but can change)") },

    resolveProtection: function(resourceProtection, parentProtection) {
        if (resourceProtection === 0) {
            return parentProtection;
        } else {
            return resourceProtection;
        }
    }
};

var IndicoSortCriteria = {
    StartTime: function(c1, c2) {
        return SortCriteria.Integer(c1.startDate.time.replaceAll(':',''),
                                    c2.startDate.time.replaceAll(':',''));
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
