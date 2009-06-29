
<div class="groupTitle"><%= _("Program description")%></div>
<table width="90%%" align="center" border="0">
    <tr>
        <td>
            <table width="100%%"><tr><td width="95%%">
            %(description)s
            </td><td>
            <form action="%(modifyDescriptionURL)s" method="POST"><input type="submit" class="btn" value="<%= _("Modify")%>"></form>
            </td></tr></table>
        </td>
    </tr>
</table>
<br>


<div class="groupTitle"><%= _("Tracks")%></div>
<table width="90%%" align="center" border="0">
    <tr>
        <td bgcolor="white" width="100%%" colspan="4" align="center">
            <form action="%(deleteItemsURL)s" method="POST">
            <br>
                %(listTrack)s
            <br>
        </td>
    </tr>
    <tr>
        <td class="buttonsSeparator" align="center" width="100%%">
            <table align="center">
                <tr>
                    <td align="center">
                            <input type="submit" class="btn" value="<%= _("remove selected")%>">   
                        </form>
                    </td>
                    <td>
                        <form action="%(addTrackURL)s" method="POST">
                            <input type="submit" class="btn" value="<%= _("add track")%>">   
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
