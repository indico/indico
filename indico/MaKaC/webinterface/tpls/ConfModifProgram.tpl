
<div class="groupTitle">${ _("Program description")}</div>
<table width="90%" align="center" border="0">
    <tr>
        <td>
            <table width="100%"><tr><td width="95%">
            ${ description }
            </td><td>
            <form action="${ modifyDescriptionURL }" method="POST"><input type="submit" class="btn" value="${ _("Modify")}"></form>
            </td></tr></table>
        </td>
    </tr>
</table>
<br>


<div class="groupTitle">${ _("Tracks")}</div>
<table width="90%" align="center" border="0">
    <tr>
        <td bgcolor="white" width="100%" colspan="4" align="center">
            <form action="${ deleteItemsURL }" method="POST">
            <br>
                ${ listTrack }
            <br>
        </td>
    </tr>
    <tr>
        <td class="buttonsSeparator" align="center" width="100%">
            <table align="center">
                <tr>
                    <td align="center">
                            <input type="submit" class="btn" value="${ _("remove selected")}">
                        </form>
                    </td>
                    <td>
                        <form action="${ addTrackURL }" method="POST">
                            <input type="submit" class="btn" value="${ _("add track")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>