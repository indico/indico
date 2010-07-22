<h2>Running</h2>
<div id="runningTable">
</div>

<h2>Waiting</h2>
<div id="waitingTable">
</div>

<script type="text/javascript">
    var runTaskTable = new TaskTable("scheduler.tasks.listRunning");
    $E('runningTable').set(runTaskTable.draw());

    var waitTaskTable = new TaskTable("scheduler.tasks.listWaiting");
    $E('waitingTable').set(waitTaskTable.draw());

</script>