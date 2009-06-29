
<div class="groupTitle"><%= _("Registration")%></div>
<table width="100%%">
    <tr>
        <td>
            <table width="100%%" align="center">
                <tr>
                    <td nowrap class="displayField"><%= _("Registration opening day")%>:</td>
                    <td width="100%%" align="left">%(startDate)s</td>
                </tr>
                <tr>
                    <td nowrap class="displayField"><%= _("Registration deadline")%>:</td>
                    <td width="100%%" align="left">%(endDate)s</td>
                </tr>
                %(usersLimit)s
                %(contactInfo)s
            </table>
        </td>
    </tr>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
            <table width="100%%" align="center">
                <tr>
                    <td><pre>%(announcement)s</pre></td>
                </tr>
            </table>
        </td>
    </tr>
	<tr>
        <td>
            <table width="100%%" align="center" style="padding-top:20px">
                <tr>
                    <td>%(actions)s</td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
