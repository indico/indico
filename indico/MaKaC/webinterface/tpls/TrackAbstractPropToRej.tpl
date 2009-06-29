<form action="%(postURL)s" method="POST">
    <table align="center" width="50%%" border="0" style="border-left: 1px solid #777777">
		<tr>
			<td class="groupTitle" colspan="2"> <%= _("Propose to be rejected")%></td>
        </tr>
        <tr>
            <td bgcolor="white" colspan="2">
				<font color="#5294CC"> <%= _("Abstract title")%>:</font><font color="gray"> %(abstractTitle)s<br></font>
                <font color="#5294CC"> <%= _("Track")%>:</font><font color="gray"> %(trackTitle)s</font>
				<br>
				<span style="border-bottom: 1px solid #5294CC; width: 100%%">&nbsp;</span>
			</td>
		</tr>
        <tr>
			<td nowrap colspan="2"><span class="titleCellFormat"> <%= _("Please enter below a comment which justifies your request")%>:</span>
                <table> 
                    <tr>
                        <td>
                            <textarea cols="50" rows="5" name="comment"></textarea>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
		<tr><td  colspan="2">&nbsp;</td></tr>
        <tr>
            <td class="buttonsSeparator" colspan="2" align="center" style="padding:10px">
                <input type="submit" class="btn" name="OK" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>
