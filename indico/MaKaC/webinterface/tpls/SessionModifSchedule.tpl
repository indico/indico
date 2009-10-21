<% declareTemplate(newTemplateStyle=True)%>

<div id="timetableDiv" style="position: relative;">

<div class="timetablePreLoading" style="width: 700px; height: 300px;">
    <div class="text" style="padding-top: 200px;">&nbsp;&nbsp;&nbsp;<%= _("Building timetable...") %></div>
</div>

<div class="clearfix"></div>

<script type="text/javascript">
var ttdata = <%= str(ttdata).replace('%','%%') %>;
var eventInfo = <%= eventInfo %>;
var timetable = new TimeTableManagement(ttdata, eventInfo, 900,$E('timetableDiv'), false, true);

IndicoUI.executeOnLoad(function(){


  $E('timetableDiv').set(timetable.draw());
  timetable.postDraw();

});
</script>
