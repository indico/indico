<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Modifying social event (basic data)")}</td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Title")}</span></td>
            <td align="left"><input type="text" name="title" size="60" value="${ title }"></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Description")}</span></td>
            <td align="left"><textarea name="description" cols="70" rows="10">${ description }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Introduction sentence")}</span></td>
            <td align="left"><textarea name="intro" cols="70" rows="2">${ intro }</textarea></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Selection type")}</span></td>
            <td align="left">
                <select name="selectionType">
                <% stl=socEvent.getSelectionTypeList() %>
                % for se in stl.keys(): 
                    <% check="" %>
                    % if se == socEvent.getSelectionTypeId(): 
                        <% check="selected" %>
                    % endif
                        <option value="${se}" ${check}>${stl[se]}</option>
                % endfor
                </select>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" class="btn" value="${ _("OK")}">&nbsp;<input type="submit" class="btn" value="${ _("cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>