
/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

function is_valid_int(s) {
    var i = parseInt(s, 10);
    return !(i.toString() == 'NaN' || ((i.toString() != s) && ('0' + i.toString() != s ) ));

}


// Returns true if and only if specified values create a valid date.
// Pass it day, month and year as strings, like taken from the form.
function is_valid_date(day, month, year) {
    if (!is_valid_int(day) || !is_valid_int(month) || !is_valid_int(year)) {
        return false;
    }

    var dayl = parseInt(day, 10);
    var monthl = parseInt(month, 10) - 1;
    var yearl = parseInt(year, 10);
    var dteDate = new Date(yearl, monthl, dayl);

    if (dteDate.valueOf().toString() == 'NaN') {
        return false;
    }

    return dayl == dteDate.getDate() && monthl == dteDate.getMonth() && yearl == dteDate.getFullYear();
}


// Returns true if and only if specified time (string) represents
// a valid hh:mm time, where hh in <0,24> and mm in <0,59>.
function is_valid_time(time) {
    var TIME_PATTERN = /^(\d){1,2}\:(\d){1,2}$/;

    if ((time).match(TIME_PATTERN) === null) {
        return false;
    }

    var ix = time.indexOf(':');
    var hour = parseInt(time.substr(0, ix), 10);
    var minute = parseInt(time.substr(ix + 1, 2), 10);
    return (hour >= 0 && hour <= 23 && minute >= 0 && minute < 60);

}


// Returns true if and only if sTime is before eTime.
// Pass it two strings of hh:mm format.
function isBefore(sTime, eTime) {
    var sDTime = new Date();
    var eDTime = new Date();

    // sTime
    var ix = sTime.indexOf(':');
    var hour = parseInt(sTime.substr(0, ix), 10);
    var minute = parseInt(sTime.substr(ix + 1, 2), 10);

    sDTime.setHours(hour);
    sDTime.setMinutes(minute);
    sDTime.setSeconds(0);

    // eTime
    ix = eTime.indexOf(':');
    hour = eTime.substr(0, ix);
    minute = eTime.substr(ix + 1, 2);

    hour = parseInt(hour, 10);
    minute = parseInt(minute, 10);
    eDTime.setHours(hour);
    eDTime.setMinutes(minute);
    eDTime.setSeconds(0);

    return sDTime.valueOf() < eDTime.valueOf();
}


function required_fields(fieldNames) {
    var isValid = true;
    for (var i = 0; i < fieldNames.length; ++i) {
        var fieldName = fieldNames[i];
        if (trim($('#' + fieldName).val()).length === 0) {
            $('#' + fieldName).addClass('invalid');
            isValid = false;
        }
    }
    return isValid;
}


function valid_email(emailString) {
    return (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(emailString));
}


// GENERAL PURPOSE => LATER WILL GO TO ANOTHER JS FILE
function findPos(obj) {
        var curleft = 0, curtop = 0;
        if (obj.offsetParent) {
                curleft = obj.offsetLeft;
                curtop = obj.offsetTop;
                while (obj = obj.offsetParent) {
                        curleft += obj.offsetLeft;
                        curtop += obj.offsetTop;
                }
        }
        return [curleft,curtop];
}

// Koch
function add_load_event(func) {
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = func;
  } else {
    window.onload = function() {
      if (oldonload) {
        oldonload();
      }
      func();
    };
  }
}

function validate_allow(allow) {
    var isValid = true;
    if (allow !== 0) {
        // eDate
        if (!is_valid_date($('#eDay').val(), $('#eMonth').val(), $('#eYear').val())) {
            $('#edate').addClass('invalid');
            isValid = false;
        }

        var eDate = new Date(parseInt($('#eYear').val(), 10),
                             parseInt($('#eMonth').val(), 10) - 1,
                             parseInt($('#eDay').val(), 10));

        if (isValid) {
            var allowDate = new Date();
            var allowDays = 0;
            allowDate.setHours(0, 0, 0, 0);
            allowDate.setDate(allowDate.getDate() + allow);
            if (eDate.valueOf() > allowDate.valueOf()) {
                IndicoUtil.markInvalidField($E('edate'),$T("This room cannot be booked more than ") + allow + $T(" days in advance"), false);
                IndicoUtil.markInvalidField($E('sdate'),$T("This room cannot be booked more than ") + allow + $T(" days in advance"), false);
                isValid = false;
            }
        }
    }

    return isValid;
}
