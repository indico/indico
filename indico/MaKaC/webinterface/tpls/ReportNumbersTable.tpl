<div id="reportNumbers" style="margin-bottom: 10px;">
  <div id="reportNumbersContainer" style="margin-bottom: 10px;"></div>
</div>
<script type="text/javascript">
    $("#reportNumbersContainer").html(new ReportNumberEditor("${addAction}","${deleteAction}", ${ jsonEncode(items) }, ${jsonEncode(reportNumberSystems)}, ${params}).draw());
</script>