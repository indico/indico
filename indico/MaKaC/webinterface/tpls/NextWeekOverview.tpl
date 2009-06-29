<% 
    """
        Oberve that this template is currently never used since
        the option for choosing the next 7 days in the category
        overview has been removed.
    """
%>

%>
<table width="100%%" align="center">
    <tr>
        <td align="center"><b>%(startDate)s -&gt; %(endDate)s</b></td>
    </tr>
    <tr>
        <td align="center">
            <table border="1">
                <tr>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date0)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date1)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date2)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date3)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date4)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date5)s</font>
                    </td>
                    <td bgcolor="green" nowrap align="center">
                        <font color="white">%(date6)s</font>
                    </td>
                </tr>
                <tr>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item0)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item1)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item2)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item3)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item4)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item5)s
                        </table>
                    </td>
                    <td bgcolor="gray" valign="top">
                        <table width="100%%">
                            %(item6)s
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
