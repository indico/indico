<div class="container">
    <div class="categoryHeader">
        <ul>
            <li><a href="<%= categDisplayURL %>"><%= _("Go back to category page") %></a></li>
        </ul>
        <h1 class="categoryTitle" style="margin-bottom: 0; border: none;">
            <%= categoryTitle %>&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(<%= _("events overview") %>)</span>
        </h1>
    </div>

<!--  old version of an overeview with vertical options bar
    <div class="topBar">
        <div class="content"">

            <form action="%(postURL)s" id="optionsForm" method="GET">
            <h1 style="display: inline; padding-right: 50px;"><%= _("Display options") %></h1>

            %(locator)s

            <%= _("Period")%>:&nbsp;
                        <select name="period" style="margin-right: 30px; font-size: 10pt; min-width: 70px;">
                            <option value="day" %(selDay)s> <%= _("day")%></option>
                            <option value="week" %(selWeek)s> <%= _("week")%></option>
                            <option value="month" %(selMonth)s> <%= _("month")%></option>
                        </select>
            <%= _("Details level")%>:&nbsp; <span><select name="detail" style="margin-right: 30px; font-size: 10pt;  min-width: 70px;">
                            %(detailLevelOpts)s
                        </select></span>
            <%= _("Date")%>:&nbsp;
                        <span id="datePlace" style="margin-right: 30px; font-size: 10pt;"></span>
                        <input type="hidden" id="day" name="day" value="<%= day %>" />
                        <input type="hidden" id="month" name="month" value="<%= month %>" />
                        <input type="hidden" id="year" name="year" value="<%= year %>" />

                <input type="submit" class="btn" value="<%= _("apply")%>" >

            </form>
            <% if key: %>
                <div style="display: none;">
                <h1><%= _("Legend") %></h1>
                <div style="margin: 10px 0 30px 10px;">%(key)s</div>
                </div>
            <% end %>
        </div>
    </div>

    <div>

        <div class="categoryOverview">
            %(overview)s
        </div>
    </div>

</div>
-->
    <table width = "100%%" cellSpacing = 3 cellPadding = 2>
        <tbody>
            <tr>
                <td valign="top">
                    <table width = "100%%">
                        <tr><td height = 15></td></tr>
                        <tr><td width = "100%%" valign = "top">
                            <div style="margin-top: 30px; float: none; width: 100%%" class="sideBar clearfix">
                                <div class="leftCorner"></div>
                                <div class="rightCorner"></div>
                                <div class="content"">

                                    <form action="%(postURL)s" id="optionsForm" name="optionsForm" method="GET">
                                    <h1 style="display: inline; padding-right: 50px;"><%= _("Display options") %></h1><br>

                                    %(locator)s<br>

                                    <%= _("Period")%>:<br>
                                                <select name="period" onchange="javascript:submitForm()" style="margin-right: 30px; font-size: 10pt; min-width: 100%%; margin-bottom: 10px">
                                                    <option value="day" %(selDay)s> <%= _("day")%></option>
                                                    <option value="week" %(selWeek)s> <%= _("week")%></option>
                                                    <option value="month" %(selMonth)s> <%= _("month")%></option>
                                                </select><br>
                                    <%= _("Details level")%>:<br> <span><select name="detail" onchange="javascript:submitForm()" style="margin-right: 30px; font-size: 10pt;  min-width: 100%%; margin-bottom: 10px">
                                                    %(detailLevelOpts)s
                                                </select></span><br>
                                    <%= _("Date")%>:<br>
                                                <span id="calendar-container"></span>
                                                <input type="hidden" id="dateContainer" name="dateContainer" />
                                                <input type="hidden" id="day" name="day" value="<%= day %>" />
                                                <input type="hidden" id="month" name="month" value="<%= month %>" />
                                                <input type="hidden" id="year" name="year" value="<%= year %>" />

                                    </form>
                                    <% if key: %>
                                        <br><h1><%= _("Legend") %>:</h1>
                                        <div style="margin: 10px 0 30px 10px;">%(key)s</div>
                                    <% end %>
                                </div>
                            </div>
                        </td></tr>
                    </table>
                </td>
                <td valign = "top">
                    <div>

                        <div class="categoryOverview">
                            %(overview)s
                        </div>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</div>

<script type="text/javascript">

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
        flat : "calendar-container",
        flatCallback :  dateChanged
    });

</script>
