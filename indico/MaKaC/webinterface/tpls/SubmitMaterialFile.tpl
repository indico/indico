<table>
<tr>
    <td class="groupTitle">${ itemNumber }</td>
    <td>
        <table>
        <tr>
            <td>Type:
                <select name="${ materialTypeSelectFieldName }">
                    ${ matTypeItems }
                </select>
                or <input name="${ materialTypeInputFieldName }" size="25" value="${ materialTypeInputFieldValue }">
            </td>
        </tr>
        <tr>
            <td>${ _("File to upload")}:
                <input type="file" name="${ fileFieldName }" size="50"><br>
                 ${ _("Rename it to")}:
                <input name="${ fileNewName }" size="25" value="${ fileName }">
            </td>
        </tr>
        </table>
    </td>
</tr>
</table>
