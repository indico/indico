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
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date0 }
                    </td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date1 }
                    </td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date2 }
                    </td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date3 }
                    </td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date4 }
                    </td>
                    % if not isWeekendFree:
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date5 }
                    </td>
                    <td style="background-color: #444; color: white; text-align: center" nowrap>
                        ${ date6 }
                    </td>
                    % endif
                </tr>
                <tr>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                                ${ item0 }
                        </table>
                    </td>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item1 }
                        </table>
                    </td>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item2 }
                        </table>
                    </td>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item3 }
                        </table>
                    </td>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item4 }
                        </table>
                    </td>
                    % if not isWeekendFree:
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item5 }
                        </table>
                    </td>
                    <td bgcolor="#ECECEC" valign="top">
                        <table width="100%">
                            ${ item6 }
                        </table>
                    </td>
                    % endif
                </tr>
            </table>
        </td>
    </tr>
</table>
