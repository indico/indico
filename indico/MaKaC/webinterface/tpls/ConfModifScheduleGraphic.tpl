<% declareTemplate(newTemplateStyle=True)%>


<div class="groupTitleNoBorder"><%= _("Timetable")%> <em>(<%=_("from")+" "%> <%= start_date %> <%=" "+_("to")+" "%> <%= end_date %> <a href=<%= editURL %>>[<%=_("edit")%>]</a> <%=_("Timezone")%>: <%= timezone %>)</em></div>
<div id="timetableDiv" style="position: relative;">

<div class="timetablePreLoading" style="width: 700px; height: 300px;">
    <div class="text" style="padding-top: 200px;">&nbsp;&nbsp;&nbsp;<%= _("Building timetable...") %></div>
</div>

<div class="clearfix"></div>

<script type="text/javascript">
var ttdata = <%= str(ttdata).replace('%','%%') %>;
var eventInfo = <%= eventInfo %>;


//Variables used to resize the timetable.
var minWidth = 600;
var widthOffset = 300;
var previousWidth = window.innerWidth - widthOffset;
var minResize = 30;

var historyBroker = new BrowserHistoryBroker();
var timetable = new TopLevelManagementTimeTable(ttdata, eventInfo, window.innerWidth - widthOffset < minWidth ? minWidth : window.innerWidth - widthOffset,$E('timetableDiv'), false, historyBroker);

IndicoUI.executeOnLoad(function(){

  $E('timetableDiv').set(timetable.draw());
  timetable.postDraw();

});

//Inefficient way of resizing a timetable
window.onresize = function (){

    //Updating only if a window was resized by certain legnth
    if(previousWidth - window.innerWidth + widthOffset > minResize || previousWidth - window.innerWidth + widthOffset < -minResize)
        //Updating only if a window size is greater than minimal timetable size
        if(timetable.width > minWidth || window.innerWidth - widthOffset > minWidth)
        {
            var newWidth = window.innerWidth - widthOffset < minWidth ? minWidth : window.innerWidth - widthOffset;
            //timetable.width = window.innerWidth - widthOffset < minWidth ? minWidth : window.innerWidth - widthOffset;
            timetable = new TopLevelManagementTimeTable(ttdata, eventInfo, newWidth, $E('timetableDiv'), false, historyBroker);
            $E('timetableDiv').set(timetable.draw());
            timetable.postDraw();
            previousWidth = newWidth;
        }
}

</script>
