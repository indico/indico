
<table width="60%" align="left" border="0" style="padding: 10px 0 0 10px;">
    <tr>
        <td class="groupTitle">${ _("Accepting abstract")}</td>
    </tr>
    <tr>
        <td bgcolor="white">
            <table>
                % if trackTitle:
                <tr>
                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Abstract title")}</span></td>
                    <td style="font-weight:bold;">${ abstractName }</td>
                </tr>
                % endif
                <tr>
                    <form action=${ acceptURL } method="POST">
                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Destination track")}</span></td>
                    <td>
                        % if not trackTitle:
                        <select name="track">
                            ${ tracks }
                        </select>
                        % else:
                        ${ trackTitle }
                        % endif
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Destination session")}</span></td>
                    <td>
                        <select name="session">
                            ${ sessions }
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Type of contribution")}</span></td>
                    <td>
                        <select name="type">
                            ${ types }
                        </select>
                    </td>
                </tr>
                <tr>

                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Comments")}</span></td>
                    <td style="padding-top: 5px; padding-bottom: 5px"><textarea name="comments" rows="6" cols="50"></textarea></td>
                </tr>
                % if showNotifyCheckbox:
                <tr>
                    <td nowrap class="titleCellTD" style="padding-top: 5px; padding-bottom: 5px"><span class="titleCellFormat">${ _("Email Notification")}</span></td>
                    <td>
                        <input type="checkbox" name="notify" value="true" checked>${ _("Send the automatic notification of acceptance using the Email Template created by the manager")}
                    </td>
                </tr>
                % endif
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td valign="bottom" align="left">
            <table valign="bottom" align="center">
                <tr>
                    <td valign="bottom" align="left">
                        <input type="submit" class="btn" name="accept" value="${ _("accept")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td valign="bottom" align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
