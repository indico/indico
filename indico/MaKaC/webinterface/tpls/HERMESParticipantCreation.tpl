<tr><td>
<table style="border-left:2px solid #777777;border-top:2px solid #777777;" width="100%">
	<tr>
        <td bgcolor="#E5E5E5">
            <input type="checkbox" name="selected_primary_authors" value=<%= auth_id %>>
        </td>
        <td bgcolor="white">
            <input type="hidden" name="auth_id" value=<%= auth_id %>>
            <%= anchor %>
            <table width="100%" border="0">
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="0" border="0">
                            <tr>
                                <td><font size="-1" color="gray"> <%= _("Title")%></font></td>
                                <td><font color="red">*</font><font size="-1" color="gray"> <%= _("Family name")%></font></td>
                                <td><font color="red">*</font><font size="-1" color="gray"> <%= _("First name")%></font></td>
                            </tr>
                            <tr>
                                <td>
                                    <select name="auth_title">
                                        <%= titleItems %>
                                    </select>
                                </td>
                                <td><input type="text" size="55" name="auth_surName" value=<%= auth_surName %>></td>
                                <td><input type="text" size="30" name="auth_firstName" value=<%= auth_firstName %>></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="0">
                            <tr>
                                <td><font color="red">*</font><font size="-1" color="gray"> <%= _("Affiliation")%></font></td>
                                <td><font color="red">*</font><font size="-1" color="gray"> <%= _("Email")%></font></td>
                                <td><font size="-1" color="gray">Phone</font></td>
                            </tr>
                            <tr>
                                <td><input type="text" size="40" name="auth_affiliation" value=<%= auth_affiliation %>></td>
                                <td><input type="text" size="40" name="auth_email" value=<%= auth_email %>></td>
                                <td><input type="text" size="14" name="auth_phone" value=<%= auth_phone %>></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <input type="hidden" name="auth_address" value="">
            </table>
        </td>
        <td bgcolor="white" nowrap>
            <input type="hidden" name="auth_primary" value=<%= auth_id %>>
            <input type="checkbox" value=<%= auth_id %> name="auth_speaker" <%= auth_speaker %>> <%= _("presenter")%>
        </td>
    </tr>
</table>
<br>
</td></tr>