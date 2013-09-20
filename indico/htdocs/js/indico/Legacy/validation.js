
/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

/*
Validation for Period Module (dates, hours and repetition)
Parameters:
- withRepeatability : whether to check 'repeatibility' field
- allowPast : whether to allow dates in the past
- what : what to validate: 0 - both dates and times, 1 - only dates, 2 - only times

Controls must follow naming conventions:
sDay, sMonth, sYear, sTime
eDay, eMonth, eYear, eTime
repeatability
*/
function validate_period(withRepeatability, allowPast, what, repeatability) {
    var DATES_AND_TIMES = 0; var ONLY_DATES = 1; var ONLY_TIMES = 2;

    if (withRepeatability === null) withRepeatability = true;
    if (allowPast === null) allowPast = false;
    if (what === null) what = DATES_AND_TIMES;

    var isValid = true;
    if (what != ONLY_TIMES) {
        // sDate
        if (!is_valid_date($('#sDay').val(), $('#sMonth').val(), $('#sYear').val())) {
            $('#sDay').addClass('invalid');
            $('#sMonth').addClass('invalid');
            $('#sYear').addClass('invalid');
            $('#sdate').addClass('invalid');
            isValid = false;
        }

        // eDate
        if (!is_valid_date($('#eDay').val(), $('#eMonth').val(), $('#eYear').val())) {
            $('#eDay').addClass('invalid');
            $('#eMonth').addClass('invalid');
            $('#eYear').addClass('invalid');
            $('#edate').addClass('invalid');
            isValid = false;
        }

        // sDate < eDate
        var sDate = new Date(parseInt($('#sYear').val(), 10), parseInt($('#sMonth').val(), 10) - 1, parseInt($('#sDay').val(), 10));
        var eDate = new Date(parseInt($('#eYear').val(), 10), parseInt($('#eMonth').val(), 10) - 1, parseInt($('#eDay').val(), 10));
        if (isValid) {
            var todayDate = new Date();
            todayDate.setHours(0, 0, 0, 0);
            if (!allowPast && (sDate.valueOf() < todayDate.valueOf())) {
                $('#sDay').addClass('invalid');
                $('#sMonth').addClass('invalid');
                $('#sYear').addClass('invalid');
                $('#sdate').addClass('invalid');
                $('#eDay').addClass('invalid');
                $('#eMonth').addClass('invalid');
                $('#eYear').addClass('invalid');
                $('#edate').addClass('invalid');
                isValid = false;
            }
        }
    }

    if (what != ONLY_DATES) {
        // sTime
        if (!is_valid_time($('#sTime').val())) {
            $('#sTime').addClass('invalid');
            isValid = false;
        }

        // eTime
        if (!is_valid_time( $('#eTime').val())) {
            $('#eTime').addClass('invalid');
            isValid = false;
        }

        // sTime < eTime
        if (!isBefore($('#sTime').val(), $('#eTime').val())) {
            $('#sTime').addClass('invalid');
            $('#eTime').addClass('invalid');
            isValid = false;
        }
    }

    // Repetition. Assume eDate >= sDate since the checking was made before
    if (withRepeatability) {
        var ms_in_one_day = 1000*60*60*24;
        var isRepeatabilityValid = true;
        var message;

        switch(repeatability) {
        // Single Day
        case "None":
            break;
        // Repeat Every Day
        case "0":
            if(Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 1) {
                isRepeatabilityValid = false;
                message = $T("Period shorter than 1 day");
            }
            break;
        // Repeat Once a Week
        case "1":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 7 ) {
                isRepeatabilityValid = false;
                message = $T("Period shorter than 1 week");
            }
            break;
        // Repeat Every Two Weeks
        case "2":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 14 ) {
                isRepeatabilityValid = false;
                message = $T("Period shorter than 2 weeks");
            }
            break;
        // Repeat Every Three Weeks
        case "3":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 21 ) {
                isRepeatabilityValid = false;
                message = $T("Period shorter than 3 weeks");
            }
            break;
        // Repeat Every Month
        // TODO: if eDate.year and sDate year are different, there could also be
        // a difference of less than one month (30-12-2009, 1-1-2010)
        case "4":
            if(eDate.getFullYear() == sDate.getFullYear() &&
                (eDate.getMonth() <= sDate.getMonth() ||
                    (eDate.getMonth() - sDate.getMonth() == 1 &&
                        eDate.getDate() < sDate.getDate() ))) {
                isRepeatabilityValid = false;
                message = $T("Period shorter than 1 month");
            }
            break;
        // Otherwise
        default:
            isRepeatabilityValid = false;
            break;
        }

        var label;
        if ($('#repeatability .label').length) {
            label = $('#repeatability .label');
        } else {
            label = $('#repeatability');
        }

        if (!isRepeatabilityValid) {
            if (typeof label.data('qtip') !== "object") {
                label.qtip({content: {text: message}});
            } else {
                label.qtip("api").set("content.text", message);
            }
            label.addClass('invalid');
            $('#edate').addClass('invalid');
            isValid = false;
        } else {
            label.removeClass('invalid');
            if (typeof label.data('qtip') === "object") {
                label.qtip("api").destroy();
            }
        }
    }

    return isValid;
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
