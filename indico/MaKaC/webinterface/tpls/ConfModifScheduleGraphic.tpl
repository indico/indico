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
var timetable = new TopLevelManagementTimeTable(ttdata, eventInfo, 900,$E('timetableDiv'), false);

IndicoUI.executeOnLoad(function(){


  $E('timetableDiv').set(timetable.draw());
  timetable.postDraw();

});
</script>
