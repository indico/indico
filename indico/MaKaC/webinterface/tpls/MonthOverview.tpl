<table width="100%" cellspacing="0" cellpadding="0" align="center">
    <tr>
        <td style="text-align: center; padding-bottom: 10px;">
            <em style="font-size: 1.3em;">${ dates }</em>
        </td>
    </tr>
    <tr>
        <td align="center">
            <table width="100%" style="border: 1px solid #AAA;" cellspacing="1" cellpadding="3">
                <tr>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay0 }</td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay1 }</td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay2 }</td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay3 }</td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay4 }</td>
                    % if not isWeekendFree:
                        <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay5 }</td>
                        <td style="background-color: #444; color: white; text-align: center" nowrap>${ nameDay6 }</td>
                    % endif
                </tr>
                % for week in month:
                    <tr>
                    <% weekday = 0 %>
                    % for day in week:
                        %if weekday < 5 or not isWeekendFree:
                            % if day is None:
                                <td></td>
                             % else:
                            <td valign="top" bgcolor="#ECECEC">
                                <table width="100%%">
                                    <tr>
                                        <td align="center">
                                            <strong style="font-size: 1.3em; color: #888;">${day.getDayNumber()}</strong>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td valign="top">${getDayCell(day)}</td>
                                    </tr>
                                </table>
                            </td>
                            % endif
                        % endif
                        <% weekday += 1 %>
                    % endfor
                    </tr>
                % endfor
            </table>
        </td>
    </tr>
</table>
