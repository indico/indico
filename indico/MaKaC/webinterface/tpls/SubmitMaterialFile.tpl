<table>
<tr>
    <td class="groupTitle">%(itemNumber)s</td>
    <td>
        <table>
        <tr>
            <td>Type:
                <select name="%(materialTypeSelectFieldName)s">
                    %(matTypeItems)s
                </select>
                or <input name="%(materialTypeInputFieldName)s" size="25" value="%(materialTypeInputFieldValue)s">
            </td>
        </tr>
        <tr>
            <td><%= _("File to upload")%>:
                <input type="file" name="%(fileFieldName)s" size="50"><br>
                 <%= _("Rename it to")%>:
                <input name="%(fileNewName)s" size="25" value="%(fileName)s">
            </td>
        </tr>
        </table>
    </td>
</tr>
</table>
