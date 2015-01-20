<div class="container" style="overflow: visible; margin:15px;">
    <div class="categoryHeader">
        <ul>
            <li><a href="${ categDisplayURL }">${ _("Go back to category page") }</a></li>
        </ul>
        <h1 class="categoryTitle">
            ${ categoryTitle | remove_tags }&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(${ _("events overview") })</span>
        </h1>
    </div>
    <table width = "100%" cellSpacing="3px" cellPadding="2px">
        <tbody>
            <tr>
                <td valign="top" style="width: 210px;">
                    <div style="margin-top: 30px; float: none; width: 100%" class="sideBar clearfix">
                        <div class="leftCorner"></div>
                        <div class="rightCorner"></div>
                        <div class="content" style="padding-right:10px;padding-left:10px;">

                            <form action="${ postURL }" id="optionsForm" name="optionsForm" method="GET">
                                ${ locator }

                                <span id="calendar-container" style="width:0px"></span>
                                <input type="hidden" id="dateContainer" name="dateContainer" value="${ "%s/%s/%s"%(day, month, year)}"/>
                                <input type="hidden" id="day" name="day" value="${ day }" />
                                <input type="hidden" id="month" name="month" value="${ month }" />
                                <input type="hidden" id="year" name="year" value="${ year }" /><br />

                                <h1 style="padding-bottom:5px;">${ _("Display options") }:</h1>
                                <table cellpadding="0" cellspacing="0" style="width:100%">
                                    <tr>
                                        <td>${ _("Period")}:</td>
                                        <td><select name="period">
                                            <option value="day" ${ selDay }> ${ _("day")}</option>
                                            <option value="week" ${ selWeek }> ${ _("week")}</option>
                                            <option value="month" ${ selMonth }> ${ _("month")}</option>
                                        </select></td>
                                    </tr>
                                    <tr>
                                        <td>${ _("Detail level")}:</td>
                                        <td><select name="detail">
                                            ${ detailLevelOpts }
                                        </select></td>
                                   </tr>
                                </table>
                            <span id="applyButtonWrapper"><input type="button" value="${ _("Apply") }" onclick="javascript:buttonSubmitForm();" /></span>

                            </form>
                            % if key:
                                <br><h1>${ _("Legend") }:</h1>
                                <div style="margin: 10px 0 30px 10px;width:180px;overflow:hidden;white-space:nowrap;">${ key }</div>
                            % endif
                        </div>
                    </div>
                </td>
                <td valign = "top">
                    <div class="categoryOverview">
                        ${ overview }
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</div>

<script type="text/javascript">

    function buttonSubmitForm() {
        var applyButtonWrapper = $E("applyButtonWrapper");
        applyButtonWrapper.set(progressIndicator(true, false));
        setTimeout(function(){
            submitForm();
        }, 30);

    }

    function submitForm()
    {
        document.optionsForm.submit();
    };


    function dateChanged(calendar){
        if(calendar.dateClicked){
            $E("day").set(calendar.date.getDate());
            $E("month").set(calendar.date.getMonth() + 1);
            $E("year").set(calendar.date.getFullYear());
            submitForm();
        }
    };

    Calendar.setup({
        inputField: $E("dateContainer").dom,
        ifFormat: IndicoDateTimeFormats.DefaultHourless,
        flat : "calendar-container",
        flatCallback :  dateChanged
    });

</script>
