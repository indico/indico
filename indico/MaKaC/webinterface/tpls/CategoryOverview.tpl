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


<script type="text/javascript">
    var date = IndicoUI.Widgets.Generic.dateField(false,null,['day', 'month', 'year'])
    date.set('<%= day %>/<%= month %>/<%= year %>');
    $E('datePlace').set(date);
</script>
