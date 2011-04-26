<table width="100%" border="0" bgcolor="white" cellpadding="1" cellspacing="1" align="center">
    <tr>
        <td valign="top" align="center">
            <table border="0" bgcolor="gray" cellspacing="1" cellpadding="1">
                <tr>
                    <td colspan="1">
                        <table border="0" cellpadding="2" cellspacing="0"
                                width="100%" class="headerselected"
                                bgcolor="#000060">
                            <tr>
                                <td width="35"><img src="${ meetingIcon }" width="32" height="32" alt="lecture" border="0"></a></td>
                                <td class="headerselected" align="left"><b><strong><font size="+2" face="arial" color="white">${ modifyIcon }${ title }</font></strong></b><br></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table border="0" bgcolor="#f0c060" cellpadding="2"
                                cellspacing="0" width="100%" class="results">
                            <tr>
                                <td valign="top" align="right"><b><strong>${ _("Date/Time:")}</strong></b></td>
                                <td><font size="-1">${ dateInterval }</font></td>
                            </tr>
                            ${ description }
                            ${ location }
                            ${ room }
                            ${ chairs }
                            ${ material }
                            ${ moreInfo }
                        </table>
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td>${ schedule }</td>
    </tr>
</table>
