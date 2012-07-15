<table align="center" width="100%">
    <tr>
        <td>
            <form id="confirmationForm" action="${ postURL }" method="POST">
                ${ passingArgs }
                <table border="0">
                    <tr>
                        <td class="groupTitle" colspan="2">
                            ${ _("Confirmation Required")}
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2">
                            <div class="bs-alert alert-toolbar">
                            ${ message }
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input type="submit" class="bs-btn bs-btn-right" name="cancel" value="${ cancelButtonCaption }">
                            <input type="submit" class="bs-btn bs-btn-right" name="confirm" value="${ confirmButtonCaption }">
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>

<script type="text/javascript">

$('#confirmationForm').submit(function(event) {
    if (${"true" if loading else "false"}) {
        if (event.originalEvent.explicitOriginalTarget.name == "confirm"){
            var killLoadProgress = IndicoUI.Dialogs.Util.progress($T("Performing action..."));
        }
    }
  });

</script>
