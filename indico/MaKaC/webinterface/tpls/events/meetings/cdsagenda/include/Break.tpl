<%page args="item, parent, minutes=False"/>

<tr class="header">
    <td align="center" valign="top" width="1%">
        <span style="font-weight:bold;">&nbsp;${getTime(item.getAdjustedStartDate(timezone))}</span>
    </td>
    <td colspan="3">
        ${item.getTitle()}
        % if formatDuration(item.getDuration()) != '00:00':
             <span class="itemDuration"> (${prettyDuration(formatDuration(item.getDuration()))}) </span>
        % endif
    </td>
</tr>
