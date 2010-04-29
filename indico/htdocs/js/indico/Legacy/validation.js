function is_valid_int( s )
{
    var i = parseInt( s, 10 )
    if ( i.toString() == 'NaN'  ||  ((i.toString() != s) && ('0'+i.toString() != s ) ) )
        return false
    return true
}

// Returns true if and only if specified values create a valid date.
// Pass it day, month and year as strings, like taken from the form.
function is_valid_date( day, month, year )
{
    if ( !is_valid_int( day )  ||  !is_valid_int( month )  ||  !is_valid_int( year ) )
        return false
    var dayl = parseInt( day, 10 );
    var monthl = parseInt( month, 10 ) - 1;
    var yearl = parseInt( year, 10 )
    var dteDate = new Date( yearl, monthl, dayl )
    if ( dteDate.valueOf().toString() == 'NaN' )
        return false
    if (
        ( dayl != dteDate.getDate() ) ||
        ( monthl != dteDate.getMonth() ) ||
        ( yearl != dteDate.getFullYear() )
       )
        return false
    return true
}
// Returns true if and only if specified time (string) represents
// a valid hh:mm time, where hh in <0,24> and mm in <0,59>.
function is_valid_time( time )
{
    var TIME_PATTERN = /^(\d){1,2}\:(\d){1,2}$/;
    if ( ( time ).match( TIME_PATTERN ) == null )
        return false
    var ix = time.indexOf( ':' )
    var hour = time.substr( 0, ix )
    var minute = time.substr( ix+1, 2 )
    var hour = parseInt( hour, 10 )
    var minute = parseInt( minute, 10 )
    if ( hour < 0 || hour > 23 )
        return false
    if ( minute < 0 || minute > 59 )
        return false
    return true
}
// Returns true if and only if sTime is before eTime.
// Pass it two strings of hh:mm format.
function isBefore( sTime, eTime )
{
    var sDTime = new Date()
    var eDTime = new Date()

    // sTime
    var ix = sTime.indexOf( ':' )
    var hour = sTime.substr( 0, ix )
    var minute = sTime.substr( ix+1, 2 )

    var hour = parseInt( hour, 10 )
    var minute = parseInt( minute, 10 )
    sDTime.setHours( hour )
    sDTime.setMinutes( minute )
    sDTime.setSeconds( 0 )

    // eTime
    ix = eTime.indexOf( ':' )
    hour = eTime.substr( 0, ix )
    minute = eTime.substr( ix+1, 2 )

    hour = parseInt( hour, 10 )
    minute = parseInt( minute, 10 )
    eDTime.setHours( hour )
    eDTime.setMinutes( minute )
    eDTime.setSeconds( 0 )

    return sDTime.valueOf() < eDTime.valueOf()
}

function required_fields( fieldNames )
{
    var isValid = true
    for ( i = 0; i < fieldNames.length; ++i )
    {
        fieldName = fieldNames[i]
        if ( trim($F( fieldName )).length == 0 )
        {
            $( fieldName ).className = 'invalid'
            isValid = false
        }
    }
    return isValid
}

function valid_email( emailString )
{
    return ( /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test( emailString ) )
}


// GENERAL PURPOSE => LATER WILL GO TO ANOTHER JS FILE

function findPos(obj) {
        var curleft = curtop = 0;
        if (obj.offsetParent) {
                curleft = obj.offsetLeft
                curtop = obj.offsetTop
                while (obj = obj.offsetParent) {
                        curleft += obj.offsetLeft
                        curtop += obj.offsetTop
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
    }
  }
}

/*
Validation for Period Module (dates, hours and repetition)
Parameters:
- f1 : form object
- withRepeatability : whether to check 'repeatibility' field
- allowPast : whether to allow dates in the past
- what : what to validate: 0 - both dates and times, 1 - only dates, 2 - only times

Controls must follow naming conventions:
sDay, sMonth, sYear, sTime
eDay, eMonth, eYear, eTime
repeatability
*/
function validate_period( f1, withRepeatability, allowPast, what )
{
    var DATES_AND_TIMES = 0; var ONLY_DATES = 1; var ONLY_TIMES = 2;

    if ( withRepeatability == null ) withRepeatability = true;
    if ( allowPast == null ) allowPast = false;
    if ( what == null ) what = DATES_AND_TIMES;

    var isValid = true;
    if ( what != ONLY_TIMES )
    {
        // sDate
        if ( !is_valid_date( $F('sDay'), $F('sMonth'), $F('sYear') ) )
        {
            f1.sDay.className = f1.sMonth.className = f1.sYear.className = f1.sdate.className = 'invalid';
            isValid = false;
        }
        // eDate
        if ( !is_valid_date( $F('eDay'), $F('eMonth'), $F('eYear') ) )
        {
            f1.eDay.className = f1.eMonth.className = f1.eYear.className = f1.edate.className = 'invalid';
            isValid = false;
        }

        // sDate < eDate
        var sDate = new Date( parseInt( $F('sYear'), 10 ), parseInt( $F('sMonth'), 10 ) - 1, parseInt( $F('sDay'), 10 ) );
        var eDate = new Date( parseInt( $F('eYear'), 10 ), parseInt( $F('eMonth'), 10 ) - 1, parseInt( $F('eDay'), 10 ) );
        if ( isValid )
        {
            todayDate = new Date();
            todayDate.setHours( 0, 0, 0, 0 );
            if ( !allowPast && ( sDate.valueOf() < (todayDate).valueOf()) )
            {
                f1.eDay.className = f1.eMonth.className = f1.eYear.className = f1.edate.className = 'invalid';
                f1.sDay.className = f1.sMonth.className = f1.sYear.className = f1.sdate.className = 'invalid';
                isValid = false;
            }
        }
    }
    if ( what != ONLY_DATES )
    {
        // sTime
        if ( !is_valid_time( $F( 'sTime' ) ) )
        {
            f1.sTime.className = 'invalid';
            isValid = false
        }
        // eTime
        if ( !is_valid_time( $F( 'eTime' ) ) )
        {
            f1.eTime.className = 'invalid';  isValid = false;
        }
        // sTime < eTime
        if ( !isBefore( $F( 'sTime' ), $F( 'eTime' ) ) )
        {
            f1.sTime.className = f1.eTime.className = 'invalid';  isValid = false;
        }
    }
    // Repetition. Assume eDate >= sDate since the checking was made before
    if ( withRepeatability ) {

        var ms_in_one_day = 1000*60*60*24;
        var isRepeatabilityValid = true;

        switch($F('repeatability')) {
        // Single Day
        case "None":
            if( sDate.valueOf() != eDate.valueOf() ) {
                isRepeatabilityValid = false;
            }
            break;
        // Repeat Every Day
        case "0":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 1 )
            {
                isRepeatabilityValid = false;
            }
            break;
        // Repeat Once a Week
        case "1":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 6 )
            {
                isRepeatabilityValid = false;
            }
            break;
        // Repeat Every Two Weeks
        case "2":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 13 )
            {
                isRepeatabilityValid = false;
            }
            break;
        // Repeat Every Three Weeks
        case "3":
            if( Math.floor((eDate.getTime() - sDate.getTime()) / ms_in_one_day) < 20 )
            {
                isRepeatabilityValid = false;
            }
            break;
        // Repeat Every Month
        // TODO: if eDate.year and sDate year are different, there could also be
        // a difference of less than one month (30-12-2009, 1-1-2010)
        case "4":
            if( eDate.getFullYear() == sDate.getFullYear() &&
                    (eDate.getMonth() <= sDate.getMonth() ||
                            (eDate.getMonth() - sDate.getMonth() == 1 &&
                                    eDate.getDate() < sDate.getDate() )))
            {
                isRepeatabilityValid = false;
            }
            break;
        // Otherwise
        default:
            isRepeatabilityValid = false;
            break;
        }

        if (!isRepeatabilityValid) {
            f1.repeatability.className = 'invalid';
            f1.edate.className = 'invalid';
            isValid = false;
        }
    }

    return isValid

}
