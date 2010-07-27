<h2>Running</h2>
<div id="runningTable">
</div>

<h2>Waiting</h2>
<div id="waitingTable">
</div>

<h2>Failed</h2>
<div id="failedTable">
</div>

<h2>Finished</h2>
<div id="finishedTable">
</div>


<script type="text/javascript">
    var runTaskTable = new TaskTable("scheduler.tasks.listRunning");
    $E('runningTable').set(runTaskTable.draw());

    var waitTaskTable = new TaskTable("scheduler.tasks.listWaiting");
    $E('waitingTable').set(waitTaskTable.draw());

    var failedTaskTable = new TaskTable("scheduler.tasks.listFailed");
    $E('failedTable').set(failedTaskTable.draw());

    var finishedTaskTable = new TaskTable("scheduler.tasks.listFinished");
    $E('finishedTable').set(finishedTaskTable.draw());

</script>