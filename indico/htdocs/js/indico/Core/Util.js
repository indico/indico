/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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

/**
 * Calls a URL with a POST request, by building and submitting a hidden form
 * @param {String} url The base url
 * @param {dictionary} getArguments A dictionary with the GET arguments, will be added to the base URL
 *                                  After adding the GET parameters we will call 'encodeURI' on the url
 *                                  This function does not handle values such as lists, etc.
 * @param {dictionary} postArgument A dictionary with the POST arguments.
 *                                  For each argument we will create a hidden field.
 * @param {String} method "post" or "get". "post" by defauly
 * @param {String} separator The separator for the GET arguments in the URL, "&" by default.
 */
Util.postRequest = function(url, getArguments, postArguments, method, separator) {

    method = any(method, "post");
    separator = any(separator, "&");

    var getUrl = url;

    if (exists(getArguments)) {
        var first = true;
        each(getArguments, function(value, key) {
            if(first) {
                getUrl += "?";
                first = false;
            } else {
                getUrl += separator;
            }
            getUrl += key + "=" + value;
        });
    }

    var form = Html.form({method: method, action: encodeURI(getUrl)});

    each(postArguments, function(value, key){
        var hiddenField = Html.input("hidden", {name: key});
        hiddenField.dom.value = value;
        form.append(hiddenField);
    });

    $E(document.body).append(form);

    form.dom.submit();
};

/**
 * Truncates a category path if it is too long.
 */
Util.truncateCategPath = function(list) {
    var first = list.slice(0,1);
    var last = list.length>1?list.slice(-1):[];
    list = list.slice(1,-1);

    var truncated = false;

    var chars = list.join('');
    while(chars.length > 10) {
        truncated = true;
        list = list.slice(1);
        chars = list.join('');
    }

    if (truncated) {
        list = concat(['...'], list);
    }

    return translate(concat(first,list,last),
               function(val) {
                   return escapeHTML(val);
               });
};
