<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="3">Configuration of Skipjack</td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">Title</span></td>
            <td align="left" colspan="2"><input type="text" name="title" size="60" value="${ title }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">URL of Skipjack</span></td>
            <td align="left" colspan="2"><input type="text" name="url" size="60" value="${ url }"></td>
        </tr>
        <tr>
            <td class="dataCaptionTD"><span class="dataCaptionFormat">Description</span></td>
            <td align="left" colspan="2"><input type="text" name="description" size="60" value="${ description }"></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="3" align="left"><input type="submit" value="OK">&nbsp;<input type="submit" value="cancel" name="cancel"></td>
        </tr>
    </table>
</form>
