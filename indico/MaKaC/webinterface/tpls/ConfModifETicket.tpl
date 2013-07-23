<br>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Current status")}</span></td>
        <td bgcolor="white" width="100%" class="blacktext" colspan="2">
            <form action="${ statusURL }" method="POST">
                <input name="changeTo" type="hidden" value="${ changeTo }">
                <b>${ status }</b>
                <small><input type="submit" value="${ changeStatus }"></small>
            </form>
        </td>
    </tr>
</table>
<br>
