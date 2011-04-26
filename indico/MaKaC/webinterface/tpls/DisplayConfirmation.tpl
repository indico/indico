<form action="${ postURL }" method="POST">
    ${ passingArgs }
    <table width="60%" align="center" border="0" style="border: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2" style="text-align:center; background:#E5E5E5; color:gray">${ _("CONFIRMATION")}</td>
        </tr>
        <tr>
            <td align="center" colspan="2" bgcolor="white" style="padding-bottom:10px">${ message }</td>
        </tr>
        <tr>
            <td style="border-top:1px solid #777777; padding-top:10px" align="center"><input type="submit" class="btn" name="confirm" value="${ confirmButtonCaption }">&nbsp;&nbsp;<input type="submit" class="btn" name="cancel" value="${ cancelButtonCaption }"></td>
        </tr>
    </table>
</form>
