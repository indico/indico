<table class="groupTable">
        <tr>
            <td colspan="5"><div class="groupTitle"><%= _("Conference creation control")%></div></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Current status")%></span></td>
        <td class="blacktext">
            <form action="%(setStatusURL)s" method="POST">
                %(locator)s
                <b>%(status)s</b>
                <small>%(changeStatus)s</small>
            </form>
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Users allowed to create conferences")%></span></td>
        <td class="blacktext"><div style="width:50%%;">%(principalTable)s</div></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Notify event creation by email to")%>:</span></td>
        <form action="%(setNotifyCreationURL)s" method="POST">
        <td class="blacktext">
        <table><tr><td><small><input name="notifyCreationList" size="30" value=%(notifyCreationList)s> ( <%= _("email addresses separated by semi-colons")%>)</small></td>
        <td align="right"><input type="submit" value="<%= _("save")%>"></td></tr></table>
        </td>
        </form>
    </tr>
</table>

