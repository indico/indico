<br>
<table width="100%">
    <tr>
        <td>
            <form action="${ postURL }" method="GET">
                ${ locator }
                <table width="95%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
                    <tr>
                        <td class="groupTitle" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp; ${ _("Display options")}</td>
                    </tr>
                    <tr>
                        <td>
                            <table width="100%" cellspacing="1" cellpadding="0">
                                <tr>
                                    <td nowrap class="displayField"><b> ${ _("Show day")}
                                            <select name="showDate">
                                                ${ availableDates }
                                            </select>
                                        </b>
                                    </td>
                                    <td nowrap class="displayField"><b> ${ _("Show session")}
                                            <select name="showSession">
                                                ${ availableSessions }
                                            </select>
                                        </b>
                                    </td>
                                </tr>
                                <tr>
                                    <td colspan="2" nowrap class="displayField">
                                        <b>${ _("Detail level")} </b>
                                            <select name="detailLevel">
                                                <option ${ DLSessionSelected }
                                                    value="session"> ${ _("session")}</option>
                                                <option ${ DLContribSelected }
                                                    value="contribution"> ${ _("contribution")}</option>
                                            </select>
                                        <b>View mode </b>
                                            <select name="viewMode">
                                                <option value="plain" ${ plainModeSelected }> ${ _("Plain")}</option>
                                                <option value="parallel" ${ parallelModeSelected }> ${ _("Parallel")}</option>
                        <option value="room" ${ roomModeSelected }> ${ _("Room")}</option>
                        <option value="session" ${ sessionModeSelected }> ${ _("Session")}</option>
                                           </select>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding-top:10px; border-top:1px solid #777777" align="center" width="100%" rowspan="3"><input type="submit" class="btn" value="${ _("apply")}">&nbsp;${ otherviewsURL }</td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>
<br>
${ timetable }
