<% import datetime %>

<script type="text/javascript">

    var dates= new WatchList();

    function verifyDates()
    {
        var ret = true;
        dates.each(function(date) {
                if (!date.processDate()) ret = false;
            });

        // TODO: check dates (startDate < endDate, etc)

        return ret;
    }

    //------ LECTURES --------

    var maxOccurrences = 9;
    var currentOccurrences = 1;
    var divDateElements = [];
    var dateFieldList = [];

    function initializeDatesContainer() {

        for (var i=1; i<maxOccurrences+1; i++) {

            var divcont = Html.div({id:"datediv"+i})
            divcont.append(Html.span({"id":"date"+i+"Place"}));
            divcont.append(Html.input("hidden",{name:"sDay_"+i, id:"sDay_"+i},""));
            divcont.append(Html.input("hidden",{name:"sMonth_"+i, id:"sMonth_"+i},""));
            divcont.append(Html.input("hidden",{name:"sYear_"+i, id:"sYear_"+i},""));
            divcont.append(Html.input("hidden",{name:"sHour_"+i, id:"sHour_"+i},"08"));
            divcont.append(Html.input("hidden",{name:"sMinute_"+i, id:"sMinute_"+i},"00"));
            divcont.append(Html.span({style:{paddingLeft:'5px', paddingRight:'5px'}}, $T("duration (in minutes):")));
            divcont.append(Html.input("text",{id:"dur_"+i, name:"dur_"+i, size:"3"},"60"));
            var remove = Html.span({id:'remove_'+i, className:'link', style:{paddingLeft:'5px'}}, $T("Remove"));
            remove.observeClick(function(event) {
                if (event.target) { // Firefox
                    var spanId = event.target.id.split('_')[1];
                } else { // IE
                    var spanId = event.srcElement.id.split('_')[1];
                }
                updateDatesContainer(spanId);
            });
            if (i != 1)
                divcont.append(remove);
            $E("datesContainer").append(divcont);
            var date = IndicoUI.Widgets.Generic.dateField(true,null,['sDay_'+i, 'sMonth_'+i, 'sYear_'+i, 'sHour_'+i, 'sMinute_'+i]);
            date.counterId = i;
            date.set('${ datetime.datetime.now().strftime("%d/%m/%Y 08:00") }');
            $E('date'+i+'Place').set(date);
            dates.append(date);
            dateFieldList.push(date);
            divDateElements.push(divcont);
            // Set visibility
            if (i != 1)
                divcont.dom.style.display = 'none';
        }
        // add new date link
        var addNewDateDiv = Html.div({style:{paddingTop:'5px'}});
        var addNewDateLink = Html.span({className:'link'}, $T("Add another occurrence for the lecture"));
        addNewDateDiv.append(addNewDateLink);
        addNewDateLink.observeClick(addNewDate);
        $E("datesContainer").append(addNewDateDiv);
    }

    function addNewDate() {
        if (currentOccurrences < maxOccurrences) {
            // check if the previous date is in correct format
            if (!verifyDates()) {
                var popup = new ErrorPopup("Invalid dates", ["${ _("Dates have an invalid format: dd/mm/yyyy hh:mm")}"], "");
                popup.open();
            } else {
                // set next date
                setNextDate();
                // show element
                divDateElements[currentOccurrences].dom.style.display = '';
                currentOccurrences += 1;
                $E('nbDates').dom.value = currentOccurrences;
            }
        } else {
            var popup = new AlertPopup($T("Adding new occurrence"), Html.span({}, $T("It is not possible to add a new occurrence for this lecture, the maximum number of occurrences is ") + maxOccurrences + "."));
            popup.open();
        }
    }

    function updateDatesContainer(datePosition) {

        // Update the date fields
        for (var i=parseInt(datePosition); i<currentOccurrences; i++) {
            $E('dur_'+i).dom.value = $E('dur_'+(i+1)).dom.value;
            dateFieldList[i-1].set(dateFieldList[i].get());
        }

        // Remove one element
        divDateElements[currentOccurrences-1].dom.style.display = 'none';
        dateFieldList[currentOccurrences-1].set('${ datetime.datetime.now().strftime("%d/%m/%Y 08:00") }');
        $E('dur_'+(currentOccurrences)).dom.value = "60";
        currentOccurrences -= 1;
        $E('nbDates').dom.value = currentOccurrences;
        verifyDates();
    }

    function setNextDate() {
        // get the previus date and convert it to Date format
        var prevDateStr = dateFieldList[currentOccurrences-1].get();
        var dateStr = prevDateStr.split(' ')[0];
        var hourStr = prevDateStr.split(' ')[1];
        var day = parseInt(dateStr.split('/')[0]);
        var month = parseInt(dateStr.split('/')[1]) - 1;
        var year = parseInt(dateStr.split('/')[2]);
        var hour = hourStr.split(':')[0];
        var min = hourStr.split(':')[1];
        var prevDate = new Date(year, month, day, hour, min);
        // date in miliseconds
        var ms = prevDate.getTime();
        var msPerDay = 24*60*60*1000;
        // calculate new date
        var nextDate = new Date();
        nextDate.setTime(ms + msPerDay);
        if (nextDate.getDate() < 10)
            day = "0" + nextDate.getDate();
        else
            day = nextDate.getDate();
        if (nextDate.getMonth()+1 < 10)
            month = "0" + (nextDate.getMonth()+1);
        else
            month = nextDate.getMonth();
        if (nextDate.getHours() < 10)
            hour = "0" + nextDate.getHours();
        else
            hour = nextDate.getHours();
        if (nextDate.getMinutes() < 10)
            min = "0" + nextDate.getMinutes();
        else
            min = nextDate.getMinutes();
        year = nextDate.getFullYear();
        var nextDateStr = day + "/" + month + "/" + year + " " + hour + ":" + min;

        // set new string date
        dateFieldList[currentOccurrences].set(nextDateStr);
        verifyDates();
    }

    //------ END LECTURES --------

</script>
