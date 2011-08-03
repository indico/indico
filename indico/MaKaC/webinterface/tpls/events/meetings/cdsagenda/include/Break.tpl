<%page args="item, parent"/>

<tr class="header">
    <td align="center" valign="top" width="2%" style="font-weight:bold;">
        ${getTime(item.getAdjustedStartDate(timezone))}&nbsp;
    </td>
    <td width="1%">
    </td>
    <td colspan="2">
        ${item.getTitle()}
        % if item.getDuration():
             <span class="itemDuration"> (${prettyDuration(item.getDuration())}) </span>
        % endif
    </td>
</tr>
