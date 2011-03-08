
<table width="80%" bgcolor="#808080" border="0" align="center">
    <tr>
        <td align="center">
            <b><font color="white" size="-1">${ _("Modification Control")}</font></b>
        </td>
    </tr>
    <tr>
        <td bgcolor="white">
            <form action=${ subCanModURL } method="POST">
                ${ subCanModStatus }
                <input type="submit" class="btn" name=${ subCanModBtnName } value=${ subCanModBtnCaption }>
            </form>
        </td>
    </tr>
</table>
