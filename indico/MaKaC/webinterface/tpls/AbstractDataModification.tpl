
<form action=%(postURL)s method="POST">
    <table width="100%%" align="center">
        <tr>
            <td>
                <table width="95%%" class="groupTable" align="center">
					<tr>
                        <td class="groupTitle"><%= _("Main data")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center">
                                <tr>
                                    <td align="right" valign="top">
                                        <span class="dataCaptionFormat"><%= _("Title")%></span>
                                        <span class="mandatoryField">*</span>
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
                <table align="center" width="95%%" class="groupTable">
                    <tr>
                        <td class="groupTitle"><%= _("Primary Authors")%></td>
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
                <table align="center" width="95%%" class="groupTable">
                    <tr>
                        <td class="groupTitle"><%= _("Co-Authors")%></td>
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
                <table align="center" width="95%%" class="groupTable">
                    <tr>
                        <td class="groupTitle"><%= _("Track classification")%>&nbsp;%(tracksMandatory)s</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table class="groupTable" align="center" width="80%%">
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
                <table align="center" width="95%%" class="groupTable">
                    <tr>
                        <td class="groupTitle"><%= _("Comments")%></td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" width="80%%">
                                <textarea name="comments" rows="8" cols="100">%(comments)s</textarea>
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
            <td align="center">
                <input type="submit" class="btn" name="validate" value="<%= _("submit")%>">
                <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
            </td>
        </tr>
    </table>
</form>

