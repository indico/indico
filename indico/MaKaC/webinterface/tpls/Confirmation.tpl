<table align="center" width="100%" class="confirmTab"><tr><td>
<form id="confirmationForm" action="${ postURL }" method="POST">
<br>
    ${ passingArgs }
    <table width="50%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2" style="text-align:center">  ${ _("CONFIRMATION")} </td>
        </tr>
        <tr>
            <td align="center" colspan="2" style="padding-bottom:10px">${ message }</td>
        </tr>
        <tr>
            <td class="buttonBar" align="center">
        <input type="submit" class="btn" name="confirm" value="${ confirmButtonCaption }">
        <input type="submit" class="btn" name="cancel" value="${ cancelButtonCaption }">
        </td>
        </tr>
    </table>
</form>
<br>
</td></tr></table>

<script type="text/javascript">

$('#confirmationForm').submit(function(event) {
    if (${"true" if loading else "false"}) {
        if (event.originalEvent.explicitOriginalTarget.name == "confirm"){
            var killLoadProgress = IndicoUI.Dialogs.Util.progress($T("Performing action..."));
        }
    }
  });

</script>
