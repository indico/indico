
<form action=%(postURL)s method="POST">
    <table width="100%%" align="center">
        <tr>
            <td style="padding-left:25px"><font color="gray"> <%= _("Please note that fields marked with * are mandatory.")%> </font><br><br>
            </td>
        </tr>
        <tr>
            <td>
                <table width="95%%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
					<tr>
                        <td class="groupTitle" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp;<%= _("Main data")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center">
                                <tr>
                                    <td align="right" valign="top">
                                        <font color="red">*</font><font color="gray"><%= _("Title")%></font> 
                                    </td>
                                    <td>
                                        <input type="text" size="100" name="title" value=%(title)s>
                                    </td>
                                </tr>
                                %(additionalFields)s
                                %(types)s
                            </table>
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
				</table>
			</td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%%" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
                    <tr>
                        <td class="groupTitle" colspan="8" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp;<%= _("Primary Authors")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table cellspacing="1" align="center">
                                %(primary_authors)s
                            </table>
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="submit" class="btn" name="add_primary_author" value="<%= _("new primary author")%>">
                            <input type="submit" class="btn" name="remove_primary_authors" value="<%= _("remove selected primary authors")%>">
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
				</table>
			</td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%%" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
                    <tr>
                        <td class="groupTitle" colspan="8" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp;<%= _("Co-Authors")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table cellspacing="1" align="center">
                                %(secondary_authors)s
                            </table>
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td align="center">
                            <input type="submit" class="btn" name="add_secondary_author" value="<%= _("new co-author")%>">
                            <input type="submit" class="btn" name="remove_secondary_authors" value="<%= _("remove selected co-authors")%>">
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
				</table>
			</td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%%" border="0" style="border-left: 1px solid #777777;" cellpadding="0" cellspacing="0">
                    <tr>
                        <td class="groupTitle" colspan="8" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp;%(tracksMandatory)s<%= _("Track classification")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" width="80%%">
                                %(tracks)s
                            </table>
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
				</table>
			</td>
        </tr>
        <tr>
            <td>
                <table align="center" width="95%%" border="0" style="border-left: 1px solid #777777;border-bottom: 1px solid #777777;" cellpadding="0" cellspacing="0">
                    <tr>
                        <td class="groupTitle" colspan="8" style="background:#E5E5E5; color:gray">&nbsp;&nbsp;&nbsp;<%= _("Comments")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" width="80%%">
                                <textarea name="comments" rows="8" cols="80">%(comments)s</textarea>
                            </table>
                        </td>
                    </tr>
					<tr>
                        <td>&nbsp;</td>
                    </tr>
				</table>
			</td>
        </tr>
        <tr>
            <td style="padding-left:25px"><br>
                <font color="gray"> <%= _("Please note that fields marked with * are mandatory.")%> </font><br>
            </td>
        </tr>
        <tr>
            <td align="center">
                <input type="submit" class="btn" name="validate" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>

