<table align="center" width="100%">
    <tr>
        <td>
            <form id="confirmationForm" action="${postURL}" method="POST">
                ${passingArgs}
                <table border="0">
                    <tr>
                        <td colspan="2">
                            <div class="titleWarning">
                                ${ _("Confirmation Required")}
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2">
                                <% new_format = 'challenge' in message %>
                                % if new_format:
                                    % if 'important' in message:
                            <div class="bs-alert alert-warning">
                                    % else:
                            <div class="bs-alert alert-toolbar">
                                    % endif
                                <div class="toolbar-container">
                                    <div class="container-title">
                                        ${message['challenge']}
                                    </div>
                                    <div style="font-weight:bold;">
                                        ${message['target']}
                                    </div>
                                    % if message['subtext']:
                                    <div>
                                        ${message['subtext']}
                                    </div>
                                    % endif
                                </div>
                                <div class="toolbar-clearer"></div>
                                % else:
                            <div class="bs-alert alert-toolbar">
                                    ${message}
                                % endif
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
