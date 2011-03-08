<table width="70%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="3">${ _("Move Contribution")}</td>
    </tr>
    <tr>
        <td bgcolor="white" width="100%">
            <table align="center" width="100%">
                <tr>
                    <form style="padding:0px;margin:0px;" action="${ moveURL }" method="POST">
                    <td align="center">
                        <input name="confId" type="hidden" value="${ confId }">
                        <input name="contribId" type="hidden" value="${ contribId }">
                        ${ _("Move this contribution to the")} :
                        <select name="Destination" size="1" >
                          % if sessionList == "":
                            <option value="--no-sessions--"> ${ _("--no sessions--") }</option>
                          % else:
                            ${ sessionList }
                          % endif
                        </select>
                    </td>
                </tr>
                <tr>
                    <td align="left" width="100%">
                        <table align="left" valign="bottom" cellspacing="0" cellpadding="0">
                            <tr>
                                <td align="left" valign="bottom">
                                    <input id="moveButton" type="submit" class="btn" value="${ _("move")}">
                                    </form>
                                </td>
                                <td align="left" valign="bottom">
                                    <form style="padding:0px;margin:0px;" action="${ cancelURL }" method="POST">
                                      <input type="submit" class="btn" value="${ _("cancel")}">
                                </td>
                            </tr>
                        </table>
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
<script>
$E("moveButton").dom.disabled = (sessionList == "");
</script>
