<div class="groupTitleNoBorder">${ _("Timetable")} <em>(${ _("from") } ${ start_date } ${ _("to") } ${ end_date } <a href=${ editURL }>[${_("edit")}]</a> ${_("Timezone")}: ${ timezone })</em></div>

<div id="timetableDiv" style="position: relative;" data-mode="management">

<div class="timetablePreLoading" style="width: 700px; height: 300px;">
    <div class="text" style="padding-top: 200px;">&nbsp;&nbsp;&nbsp;${ _("Building timetable...") }</div>
</div>

<div class="clearfix"></div>

<script type="text/javascript">
var ttdata = ${ ttdata | n,j };
var eventInfo = ${eventInfo | n,j };


//Variables used to resize the timetable.
var widthOffset = 300;

$(function() {
    var historyBroker = new BrowserHistoryBroker();
    var timetable = new TopLevelManagementTimeTable(ttdata, eventInfo, document.body.clientWidth - widthOffset,$E('timetableDiv'), false, historyBroker, false, ${ customLinks });

    $E('timetableDiv').set(timetable.draw());
    timetable.postDraw();
});
</script>