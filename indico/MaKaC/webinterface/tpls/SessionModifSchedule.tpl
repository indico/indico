<div id="timetableDiv" style="position: relative;">

<div class="timetablePreLoading" style="width: 700px; height: 300px;">
    <div class="text" style="padding-top: 200px;">&nbsp;&nbsp;&nbsp;${ _("Building timetable...") }</div>
</div>

<div class="clearfix"></div>

<script type="text/javascript">
var ttdata = ${ str(ttdata) };
var eventInfo = ${ eventInfo };

$(function() {

    var minWidth = 900;
    var widthOffset = 300;
    var historyBroker = new BrowserHistoryBroker();
    var timetable = new SessionManagementTimeTable(ttdata, eventInfo, document.body.clientWidth - widthOffset < minWidth ?
                                                   minWidth:
                                                   document.body.clientWidth - widthOffset,$E('timetableDiv'),historyBroker);
    $E('timetableDiv').set(timetable.draw());
    timetable.postDraw();
});

</script>
