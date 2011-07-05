<%
    """
        Oberve that this template is currently never used since
        the option for choosing the next 7 days in the category
        overview has been removed.
    """
%>

<table width="100%" align="center">
    <tr>
        <td align="center"><b>${ startDate } -&gt; ${ endDate }</b></td>
    </tr>
    <tr>
        <td align="center">
            <table border="1">
                <tr>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date0 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date1 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date2 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date3 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date4 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date5 }</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">${ date6 }</font>
                    </td>
                </tr>
                <tr>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item0 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item1 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item2 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item3 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item4 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item5 }
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%">
                            ${ item6 }
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
