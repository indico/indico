<%page args="item, parent"/>

<tr class="header">
    <td align="center" valign="top" width="2%" style="font-weight:bold;">
        ${getTime(item.getAdjustedStartDate(timezone))}&nbsp;
    </td>
    <td width="1%">
    </td>
    <td colspan="2">
        ${item.getTitle()}
        % if formatDuration(item.getDuration()) != '00:00':
             <span class="itemDuration"> (${prettyDuration(formatDuration(item.getDuration()))}) </span>
        % endif
    </td>
</tr>
