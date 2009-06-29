<table align="center" style="border-top:1px solid #777777;
                                border-left:1px solid #777777;
                                background:#D9D9D9;"
                                width="90%%">
    <tr>
        <td align="left" width="33%%">%(dateInterval)s</td>
        <td align="center" width="33%%">%(place)s</td>
        <td align="right" width="33%%">%(name)s</td>
    </tr>
    <tr style="background:white">
        <form action=%(remEntriesURL)s method="POST">
        <td colspan="3">
            <table width="90%%" align="center">
                %(entries)s
            </table>
        </td>
    </tr>
    <tr>
        <td align="left" colspan="3">
            <table>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td> 
                                    <input type="submit" class="btn" value="<%= _("remove selected")%>">
                                </td>
								</form>
								<form action=%(addContribURL)s method="POST">
                                <td>
                                    <input type="submit" class="btn" value="<%= _("add contribution")%>">
                                </td>
								</form>
								<form action=%(addBreakURL)s method="POST">
                                <td>
                                    <input type="submit" class="btn" value="<%= _("add break")%>">
                                </td>
								</form>
								<form action=%(compactURL)s method="POST">
                                <td>
									<input type="submit" class="btn" value="<%= _("compact")%>">
								</td>
								</form>
                            </tr>
                        </table>
                    </td>
                    <td align="right" width="100%%">
                        <table>
                            <tr>
								<form action=%(delSlotURL)s method="POST">
                                <td>
									<input type="submit" class="btn" value="<%= _("delete this slot")%>">
                                </td>
								</form>
								<form action=%(editSlotURL)s method="POST">
                                <td>
									<input type="submit" class="btn" value="<%= _("modify this slot")%>">
                                </td>
								</form>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
