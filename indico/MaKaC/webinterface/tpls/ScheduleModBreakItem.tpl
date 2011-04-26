<tr>
    <td nowrap valign="top"><input type="checkbox" name="selEntry" value=${ id }></td>
    <td nowrap valign="top">${ date }</td>
    <td nowrap valign="top">${ duration }</td>
    <td width="100%" align="center">--${ caption }--</td>
    <td valign="top">
        <table cellpadding="1" cellspacing="0">
            <tr>
                <td>
                    <a href=${ moveUpURL }><img src=${ upArrowURL } border="0" alt=" ${ _("move entry before the previous one")}"></a>
                </td>
                <td>
                    <a href=${ moveDownURL }><img src=${ downArrowURL } border="0" alt=" ${ _("move entry after the next one")}"></a>
                </td>
            </tr>
        </table>
    </td>
</tr>
<tr>
    <td colspan="5" style="border-bottom:1px solid gray">&nbsp;</td>
</tr>
