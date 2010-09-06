
<tr><td style="padding-bottom: 20px;">
<table style="-moz-border-radius: 5px 5px 5px 5px; border:1px solid #999999;" width="100%%" cellspacing="0" cellpadding="0">
    <tr>
        <td bgcolor="#E5E5E5" style="-moz-border-radius-bottomleft: 5px; -moz-border-radius-topleft: 5px;">
            <input type="checkbox" name="selected_secondary_authors" value="%(auth_id)s">
        </td>
        <td bgcolor="white" style="-moz-border-radius-bottomright: 5px; -moz-border-radius-topright: 5px;">
            <input type="hidden" name="auth_id" value="%(auth_id)s">
            %(anchor)s
            <table width="100%%" border="0" style="padding:10px;">
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="2" border="0">
                            <tr>
                                <td><span class="subDataCaptionFormat"> <%= _("Title")%></span></td>
                                <td><span class="subDataCaptionFormat"> <%= _("Family name")%></span><span class="mandatoryField">&nbsp;*</span></td>
                                <td><span class="subDataCaptionFormat"> <%= _("First name")%></span><span class="mandatoryField">&nbsp;*</span></td>
                            </tr>
                            <tr>
                                <td>
                                    <select name="auth_title">
                                        %(titleItems)s
                                    </select>
                                </td>
                                <td><input type="text" size="30" name="auth_surName" value=%(auth_surName)s></td>
                                <td><input type="text" size="20" name="auth_firstName" value=%(auth_firstName)s></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="2" style="padding:3px;">
                            <tr>
                                <td><span class="subDataCaptionFormat"> <%= _("Affiliation")%></span><span class="mandatoryField">&nbsp;*</span></td>
                                <td><span class="subDataCaptionFormat"> <%= _("Email")%></span><span class="mandatoryField">&nbsp;*</span></td>

                            </tr>
                            <tr>
                                <td><input type="text" size="28" name="auth_affiliation" value=%(auth_affiliation)s></td>
                                <td><input type="text" size="30" name="auth_email" value=%(auth_email)s></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table cellpacing="0" cellpadding="2">
                            <tr>
                                <td><span class="subDataCaptionFormat"><%= _("Phone")%></span></td>
                            </tr>
                            <tr>
                                <td><input type="text" size="14" name="auth_phone" value=%(auth_phone)s></td>
                                <td bgcolor="white" nowrap id="tdSecondaryPresenter<%= auth_id %>" class="<% if auth_speaker == 'checked': %>tdSelected<%end%><%else:%>tdNotSelected<%end%>" style="-moz-border-radius: 5px 5px 5px 5px; padding-right:6px; width:100%%;">
                                    <input type="checkbox" id="secondary_auth_speaker<%= auth_id %>" name="auth_speaker" value="%(auth_id)s" %(auth_speaker)s onClick="switchSecondaryAuthorBackground('<%= auth_id %>')"> <%= _("This co-author will be also a <b>presenter</b>")%>
                               </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <input type="hidden" name="auth_address" value="%(auth_id)s">
            </table>
        </td>

    </tr>
</table>
</td></tr>
<script>
    function switchSecondaryAuthorBackground(id) {
        if ($E('secondary_auth_speaker'+id).get()) {
            $E('tdSecondaryPresenter'+id).dom.className = "tdSelected"
        }else {
            $E('tdSecondaryPresenter'+id).dom.className = "tdNotSelected"
        }
    }
</script>
