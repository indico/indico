<div id="timetable" style="position: relative;">

<div class="timetablePreLoading" style="width: 700px; height: 300px;">
    <div class="text" style="padding-top: 200px;">&nbsp;&nbsp;&nbsp;${ _("Building timetable...") }</div>
</div>

<div class="clearfix"></div>

<script type="text/javascript">

IndicoUI.executeOnLoad(function(){
  var ttdata = ${ ttdata };
  var eventInfo = ${ eventInfo | n,j };

  var historyBroker = new BrowserHistoryBroker();
  var timetableLayout = ${ "'%s'"%timetableLayout };
  if (timetableLayout === '') {
      timetableLayout = null;
  }
  var timetable = new TopLevelDisplayTimeTable(ttdata,eventInfo,710,$E('timetable'), 'session', historyBroker, timetableLayout);
  $E('timetable').set(timetable.draw());
  timetable.postDraw();
});

$.ui.sticky({
    sticky: nothing,
    normal: nothing
});

</script>
