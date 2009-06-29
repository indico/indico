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
            <td> <%= _("URL to File")%>:
                <input name="%(urlFieldName)s" value="%(linkValue)s">
            </td>
        </tr>
        </table>
    </td>
</tr>
</table>
