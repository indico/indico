<% import datetime %>

<script type="text/javascript">
    var dates = new WatchList();

    function verifyDates() {
        var ret = true;
        dates.each(function(date) {
            if (!date.processDate()) {
                ret = false;
            }
        });
        return ret;
    }

    function isDateValid(date) {
        // ZODB-specific, should be changed once the DB is migrated
        var minDate = new Date('1901-12-13T21:45:52+00:00');
        var maxDate = new Date('2038-01-19T04:14:07+00:00');
        return minDate <= date && date <=  maxDate;
    }

    function showDatesStorageErrorPopup(startDate, endDate) {
        // Show a pop-up if the start or end dates are outside the range which
        // can be stored in the database.
        // Change once DB is migrated
        var errorMsgs = [];

        if (!isDateValid(startDate)) {
            errorMsgs.push($T("The start date is invalid."));
        }
        if (!isDateValid(endDate)) {
            errorMsgs.push($T("The end date is invalid."));
        }
        if (errorMsgs.length) {
            var popupTitle = errorMsgs.length === 1 ? $T("Invalid date") : $T("Invalid dates");
            var popup = new ErrorPopup(popupTitle, errorMsgs, "");
            popup.open();
        }
        return !!errorMsgs.length;
    }

    var advOptSwitch = true;
    function showAdvancedOptions() {
        if (advOptSwitch) {
            $('#advancedOptions').hide();
            $('#advancedOptionsText').html($T('Show advanced options...'));
        }else {
            $('#advancedOptions').show();
            $('#advancedOptionsText').html($T('Hide advanced options...'));
        }
        advOptSwitch = !advOptSwitch;
    }
    $('#advancedOptionsText').click(showAdvancedOptions);


    //------ LECTURES --------

    var currentOccurrences = 1;
    var dateFieldList = [];

    function verifyLectureDates() {
        var ret = true;
        $.each(dateFieldList, function(i, field) {
            if (!field.processDate()) {
                ret = false;
                return false;
            }
        });
        return ret;
    }

    function showLectureDatesStorageErrorPopup() {
        // Show a pop-up if any of the start dates are outside the range which
        // can be stored in the database.
        var errorMsgs = [];
        $.each(dateFieldList, function(i, field) {
            date = Util.parseJSDateTime(field.get(), IndicoDateTimeFormats.Default);
            if (!isDateValid(date)) {
                errorMsgs.push($T("Invalid lecture date: {0}").format(date));
            }
        });

        if (errorMsgs.length) {
            var popupTitle = errorMsgs.length === 1 ? $T("Invalid date") : $T("Invalid dates");
            var popup = new ErrorPopup(popupTitle, errorMsgs, "");
            popup.open();
        }
        return !!errorMsgs.length;
    }



    function createDateContainer(num) {
        var id = _.uniqueId('lectureField_');
        var cont = $('<div/>', {'class':'dateRow'});
        var dateField = $('<span/>', {'class':'dateContainer'}).appendTo(cont);
        // Create the fields used by the date picker
        var fields = ['sDay', 'sMonth', 'sYear', 'sHour', 'sMinute'];
        $.each(fields, function(i, name) {
            $('<input/>', {
                type: 'hidden',
                name: name+'_'+num,
                id: name+'_'+id
            }).appendTo(cont);
        });
        $('#sHour_' + id).val('08');
        $('#sMinute_' + id).val('00');
        $('<span/>').css({paddingLeft:'5px', paddingRight:'5px'}).html($T('duration (in minutes):')).appendTo(cont);
        $('<input/>', {type:'text', name:'dur_'+num, size:3}).val('60').appendTo(cont);
        // "remove" link if it's not the first one
        if(num != 1) {
            $('<span/>', {'class': 'link remove'}).css('paddingLeft', '5px').html($T('Remove')).appendTo(cont);
        }
        $('#datesContainer').append(cont);
        // create date picker
        var date = IndicoUI.Widgets.Generic.dateField(true,null,['sDay_'+id, 'sMonth_'+id, 'sYear_'+id, 'sHour_'+id, 'sMinute_'+id]);
        date.set('${ datetime.datetime.now().strftime("%d/%m/%Y 08:00") }');
        $E(dateField[0]).set(date); // we need the element to be extended with processDate so we use $E
        dateFieldList.push(date);
        $('#nbDates').val(currentOccurrences);
        // use last date + 1 day
        if(num > 1) {
            var format = 'dd/MM/yyyy HH:mm';
            var date = Date.parseExact(dateFieldList[num - 2].get(), format);
            date.add({days: 1});
            dateFieldList[num - 1].set(date.toString(format));
            verifyLectureDates();
        }
    }

    $('#datesContainer').delegate('.remove', 'click', function() {
        var row = $(this).closest('.dateRow');
        $('#nbDates').val(--currentOccurrences);
        var successors = row.nextAll('.dateRow');
        dateFieldList.splice(row.index(), 1);
        row.remove();
        // update the name of all fields after the removed one
        successors.each(function() {
            var num = $(this).index() + 1;

            $('input[name]', this).attr('name', function(i, attr) {
                return attr.split(/_/)[0] + '_' + num;
            });
        });
        verifyLectureDates();
    });

    function initializeDatesContainer() {
        // create "add date" link
        var newDateDiv = $('<div/>').css('paddingTop', '5px');
        $('<span/>', {
            'class': 'link'
        }).click(function() {
            if (!verifyLectureDates()) {
                new ErrorPopup("Invalid dates", [$T('Dates have an invalid format: dd/mm/yyyy hh:mm')], "").open();
                return;
            }
            createDateContainer(++currentOccurrences);
        }).html($T('Add another occurrence for the lecture')).appendTo(newDateDiv);
        // create first date row
        createDateContainer(1);
        $('#datesContainer').after(newDateDiv);
    }
    //------ END LECTURES --------

</script>
