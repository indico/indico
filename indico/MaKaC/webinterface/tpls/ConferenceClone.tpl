<script type="text/javascript">
    var date = new Date();
    var formattedDate = Util.formatDateTime(date, IndicoDateTimeFormats.DefaultHourless);
    var dateOnce = IndicoUI.Widgets.Generic.dateField_sdate(false, null, ['stddo', 'stdmo', 'stdyo']);
    dateOnce.set(formattedDate);
    var dateInterval_start = IndicoUI.Widgets.Generic.dateField(false, null, ['inddi', 'indmi', 'indyi']);
    dateInterval_start.set(formattedDate);
    var dateInterval_until = IndicoUI.Widgets.Generic.dateField(false, null, ['stddi', 'stdmi', 'stdyi']);
    var dateDays_start = IndicoUI.Widgets.Generic.dateField(false, null, ['inddd', 'indmd', 'indyd']);
    dateDays_start.set(formattedDate);
    var dateDays_until = IndicoUI.Widgets.Generic.dateField(false, null, ['stddd', 'stdmd', 'stdyd']);


    function setCloneType(type) {
            document.getElementById('ct').value = type;
            $E('cloningForm').dom.submit();
    }

    function cloneOnceForm()
    {

        var isValid = dateOnce.processDate();

        if (isValid == true)
        {
            setCloneType('once');
        }else {
            new AlertPopup($T("Date invalid"), $T('The specified date (' + dateOnce.get() + ') is not valid.')).open();
        }

    }

    function cloneIntervalForm()
    {

        var isValid = dateInterval_start.processDate();
        var errorText = "";
        if (isValid == true) {
            if ($E("intEndDateUntil").dom.checked) {
                isValid = dateInterval_until.processDate();
                errorText = $T("The specified end date is not valid.");
            } else {
                isValid = parseInt($E("numi").dom.value) > 0;
                errorText = $T("The specified number of times is not valid.");
            }
        }else {
            errorText = $T("The specified starting date is not valid.");
        }

        if (isValid == true)
        {
            setCloneType('intervals');
        }else {
            new AlertPopup($T("Clone Error"), errorText).open();
        }

    }

    function cloneDaysForm()
    {

        var isValid = dateDays_start.processDate();
        var errorText = "";
        if (isValid == true) {
            if ($E("daysEndDateUntil").dom.checked) {
                isValid = dateDays_until.processDate();
                errorText = $T("The specified end date is not valid.");
            } else {
                isValid = parseInt($E("numd").dom.value) > 0;
                errorText = $T("The specified number of times is not valid.");
            }
        }else {
            errorText = $T("The specified starting date is not valid.");
        }

        if (isValid == true)
        {
            setCloneType('days');
        }else {
            new AlertPopup($T("Clone Error"), errorText).open();
        }

    }


    IndicoUI.executeOnLoad(function() {
        $E('cloneOncePlace').addContent(dateOnce);
        $E('cloneIntervalPlace_start').addContent(dateInterval_start);
        $E('cloneIntervalPlace_until').addContent(dateInterval_until);
        $E('cloneDaysPlace_start').addContent(dateDays_start);
        $E('cloneDaysPlace_until').addContent(dateDays_until);
    });
</script>


<div class="groupTitle">${ _("Clone the event:") } ${ confTitle }</div>


<h2>${ _("Step 1: What to clone?")}</h2>

<form id="cloningForm" action="${ cloning }" method="post">

    <div class="cloneElements">
        <input type="hidden" id="ct" name="cloneType" value="none" />
        <ul style="list-style-type: none;">
            <li><strong>${ _("Choose elements to clone:")}</strong></li>

            <li><input type="checkbox" name="cloneDetails" id="cloneDetails" checked disabled value="1"/>
                ${ _("Main information")}</li>
            <li><input type="checkbox" name="cloneMaterials" id="cloneMaterials" value="1"/>
                ${ _("Attached materials")}</li>
            <li><input type="checkbox" name="cloneAccess" id="cloneAccess" value="1" checked />
                ${ _("Access and management privileges")}</li>
            <li><input type="checkbox" name="cloneAlerts" id="cloneAlerts" checked value="1" />
                ${ _("Alarms")}</li>

            ${ cloneOptions }
        </ul>
    </div>

    <h2>${ _("Step 2: When to clone?")}</h2>

    <div style="margin-top: 10px; margin-bottom: 10px;">
        ${ _("You have the possibility to: clone the event")} <a href="#cloneOnce">${ _("once")}</a>,
        ${ _("clone it")} <a href="#cloneInterval">${ _("using a specific interval")}</a> ${ _("or")}
        <a href="#cloneDays">${ _("specific days")}</a>.
    </div>

    <div class="optionGroup">
                <h3 class="groupTitleSmall"><a name="cloneOnce"></a>${ _("Clone the event only once at the specified date")}</h3>

                <span id="cloneOncePlace">
                        <input type="hidden" id="stddo" name="stddo"/>
                        <input type="hidden" id="stdmo" name="stdmo"/>
                        <input type="hidden" id="stdyo" name="stdyo"/>
                </span>

                <input type="button" class="btn" name="cloneOnce" value="${ _("clone once")}"
                                onclick="javascript:cloneOnceForm();" />
    </div>

    <div class="optionGroup">
                <h3 class="groupTitleSmall"><a name="cloneInterval"></a>${ _("Clone the event with a fixed interval:")}</h3>

                    <div class="formLine">
                        <label for="period"> ${ _("every:")} </label>
                        <input type="text" size="3" name="period" id="period" value="1" />
                            <small>
                                <select name="freq">
                                    <option value="day">${ _("day(s)")}</option>
                                    <option value="week" selected>${ _("week(s)")}</option>
                                    <option value="month">${ _("month(s)")}</option>
                                    <option value="year">${ _("year(s)")}</option>
                                </select>
                            </small>
                    </div>
                    <div class="formLine">
                        <label> ${ _("starting:")} </label>
                        <span id="cloneIntervalPlace_start">
                            <input type="hidden" id="inddi" name="inddi"/>
                            <input type="hidden" id="indmi" name="indmi"/>
                            <input type="hidden" id="indyi" name="indyi"/>
                        </span>
                    </div>
                    <div class="formLine">
                        <input id="intEndDateUntil" type="radio" name="intEndDateChoice" value="until" checked />

                        <label> ${ _("until:")} </label>
                        <span id="cloneIntervalPlace_until">
                            <input type="hidden" id="stddi" name="stddi"/>
                            <input type="hidden" id="stdmi" name="stdmi"/>
                            <input type="hidden" id="stdyi" name="stdyi"/>
                        </span>
                        <small> ${ _("(inclusive)")} </small>

                    </div>
                    <div class="formLine">
                        <input id="intEndDateNTimes" type="radio" name="intEndDateChoice" value="ntimes" />
                        <input type="text" name="numi" id="numi" size="3" value="1" />
                        <label for="numi"> ${ _("time(s)")}</label>
                    </div>
                    <div>
                        <input type="button" class="btn" name="cloneWithInterval" value="${ _("clone with interval")}"
                                onclick="javascript:cloneIntervalForm();" />
                    </div>
        </div>
        <div class="optionGroup">
                <h3 class="groupTitleSmall"><a name="cloneDays"></a>${ _("Clone the agenda on given days:")}</h3>

                <div class="formLine">
                    <label> ${ _("on the:")} </label>
                    <select name="order">
                        <option value="1">${ _("first")}</option>
                        <option value="2">${ _("second")}</option>
                        <option value="3">${ _("third")}</option>
                        <option value="4">${ _("fourth")}</option>
                        <option value="last">${ _("last")}</option>
                    </select>
                    <select name="day">
                        <option value="0">${ _("Monday")}</option>
                        <option value="1">${ _("Tuesday")}</option>
                        <option value="2">${ _("Wednesday")}</option>
                        <option value="3">${ _("Thursday")}</option>
                        <option value="4">${ _("Friday")}</option>
                        <option value="5">${ _("Saturday")}</option>
                        <option value="6">${ _("Sunday")}</option>
                        <option value="NOVAL" disabled>---------------</option>
                        <option value="OpenDay">${ _("Open Day")}</option>
                    </select>
                        <label for="monthPeriod"> ${ _("every")} </label>
                        <input type="text" size="3" id="monthPeriod" name="monthPeriod" value="1" />
                        <label for="monthPeriod"> ${ _("month(s)")}</label>
                </div>
                <div class="formLine">
                  <label>${ _("starting:")}&nbsp;</label>
                  <span id="cloneDaysPlace_start">
                            <input type="hidden" id="inddd" name="inddd"/>
                            <input type="hidden" id="indmd" name="indmd"/>
                            <input type="hidden" id="indyd" name="indyd"/>
                  </span>
                </div>
                <div class="formLine">
                       <input id="daysEndDateUntil" type="radio" name="daysEndDateChoice" value="until" checked />
                      <label>${ _("until:")}&nbsp;</label>
                    <span id="cloneDaysPlace_until">
                            <input type="hidden" id="stddd" name="stddd"/>
                            <input type="hidden" id="stdmd" name="stdmd"/>
                            <input type="hidden" id="stdyd" name="stdyd"/>
                    </span>
                    <small> ${ _("(inclusive)")}</small>
                </div>
                <div class="formLine">
                  <input id="daysEndDateNTimes" type="radio" name="daysEndDateChoice" value="ntimes" />
                  <input type="text" name="numd" id="numd" size="3" value="1" />
                  <label> ${ _("time(s)")}</label>
                   </div>

                <input     type="button" class="btn" name="cloneGivenDays" value="${ _("clone given days")}"
                                    onclick="javascript:cloneDaysForm();" />

        </div>

</form>
