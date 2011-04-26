    <tr>
    <td class="titleCellFormat" style="border-bottom: 1px solid #888; padding-right:10px" colspan="2">
        ${ title }
        % if selectFunc:
            <img src= "${ Config.getInstance().getSystemIconURL("checkAll")}"  border="0" alt="Select all" onclick="javascript:selectAll${ id }()">
            <img src= "${ Config.getInstance().getSystemIconURL("uncheckAll")}"  border="0" alt="Select all" onclick="javascript:unselectAll${ id }()">
            <br>
        % endif
    </td>
    </tr>
    <tr><td align="left" valign="top">
    ${ "<br/>".join(options)}
    </td></tr>
