<table width="70%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="3"><%= _("Move Contribution")%></td>
    </tr>
    <tr>
        <td bgcolor="white" width="100%%">
            <table align="center" width="100%%">
                <tr>
					<form style="padding:0px;margin:0px;" action="%(moveURL)s" method="POST">
                    <td align="center">
                        <input name="confId" type="hidden" value="%(confId)s">
                        <input name="contribId" type="hidden" value="%(contribId)s">
                        <%= _("Move this contribution to the")%> :
                        <select name="Destination" size="1" >
                          %(sessionList)s
                        </select>
                    </td>
                </tr>
                <tr>
                    <td align="left" width="100%%">
						<table align="left" valign="bottom" cellspacing="0" cellpadding="0">
							<tr>
								<td align="left" valign="bottom">
									<input type="submit" class="btn" value="<%= _("move")%>">
									</form>
								</td>
								<td align="left" valign="bottom">
									<form style="padding:0px;margin:0px;" action="%(cancelURL)s" method="POST">
									  <input type="submit" class="btn" value="<%= _("cancel")%>">
								</td>
							</tr>
						</table>
                    </td>
					</form>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
