
<table class="groupTable">
    <tr>
        <td colspan="5" class="groupTitle"> <%= _("Modification control")%></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Managers")%><br><font size="-2">(<%= _("users allowed to modify")%>)</font></span></td>
        <td class="blacktext">%(principalTable)s</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Modification key")%></span></td>
        <td class="blacktext">
            <form action="%(setModifKeyURL)s" method="POST" onsubmit="if(this.modifKey.value) return confirm('<%=_("Please note that it is more secure to use the managers list instead of a modification key.")%>');">
                %(locator)s
                <input name="modifKey" type="password" size=25 value="%(modifKey)s">
                <input type="submit" class="btn" value="<%= _("change")%>">
                <div class="warningText"><%=_("Note: It is more secure to use the manager list instead of a modification key!")%></div>
            </form>
       </td>
    </tr>
</table>
