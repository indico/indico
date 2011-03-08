<% import datetime %>

<script  type="text/javascript">

    var dates= new WatchList();
    
    function setOtherLocation()
    {
        objRoom.set('other', true);    
    }
    
    function setListLocation()
    {
        objRoom.set('fromList', true);    
    }

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
    var datesCounter = 0;

    function nbDatesChanged()
    {
        var newCount = parseInt($E("nbDates").get());
        
        if (datesCounter==0){
            newCount = 1;
        }
        if (datesCounter < newCount) {
            for (var i = datesCounter+1; i<=newCount;i++) {
                var divcont = Html.div({id:"datediv"+i})
                divcont.append('${ _("date #")}'+i);
                divcont.append(Html.span({"id":"date"+i+"Place"}));
                divcont.append(Html.input("hidden",{name:"sDay_"+i, id:"sDay_"+i},""));
                divcont.append(Html.input("hidden",{name:"sMonth_"+i, id:"sMonth_"+i},""));
                divcont.append(Html.input("hidden",{name:"sYear_"+i, id:"sYear_"+i},""));
                divcont.append(Html.input("hidden",{name:"sHour_"+i, id:"sHour_"+i},"08"));
                divcont.append(Html.input("hidden",{name:"sMinute_"+i, id:"sMinute_"+i},"00"));
                divcont.append('${ _("duration (in minutes):")}');
                divcont.append(Html.input("text",{name:"dur_"+i, size:"3"},"60"));
                $E("datesContainer").append(divcont);
                var date = IndicoUI.Widgets.Generic.dateField(true,null,['sDay_'+i, 'sMonth_'+i, 'sYear_'+i, 'sHour_'+i, 'sMinute_'+i]);    
                date.counterId = i;
                date.set('${ datetime.datetime.now().strftime("%d/%m/%Y 08:00") }');
                $E('date'+i+'Place').set(date);
                dates.append(date);
            }
        }else if (datesCounter > newCount) {
            for (var i = datesCounter; i>newCount;i--) {
                $E("datesContainer").remove($E("datediv"+i));
                dates.removeAt(i-1);
            }
        }

        datesCounter = newCount;
    }
    //------ END LECTURES --------
    
</script>
