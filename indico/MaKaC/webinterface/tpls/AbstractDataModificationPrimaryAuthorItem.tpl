
<tr><td style="padding-bottom: 20px;">
<table style="-moz-border-radius: 5px 5px 5px 5px; border:1px solid #999999;" width="100%" cellspacing="0" cellpadding="0">
    <tr>
        <td bgcolor="#E5E5E5" style="-moz-border-radius-bottomleft: 5px; -moz-border-radius-topleft: 5px;">
            <input type="checkbox" name="selected_primary_authors" value="${ auth_id }">
        </td>
        <td bgcolor="white" style="-moz-border-radius-bottomright: 5px; -moz-border-radius-topright: 5px;">
            <input type="hidden" name="auth_id" value="${ auth_id }">
            ${ anchor }
            <table width="100%" border="0" style="padding:10px;">
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="2" border="0">
                            <tr>
                                <td><span class="subDataCaptionFormat"> ${ _("Title")}</span></td>
                                <td><span class="subDataCaptionFormat"> ${ _("Family name")}</span><span class="mandatoryField">&nbsp;*</span></td>
                                <td><span class="subDataCaptionFormat"> ${ _("First name")}</span><span class="mandatoryField">&nbsp;*</span></td>
                            </tr>
                            <tr>
                                <td>
                                    <select name="auth_title">
                                        ${ titleItems }
                                    </select>
                                </td>
                                <td><input type="text" size="30" name="auth_surName" value=${ auth_surName }></td>
                                <td><input type="text" size="20" name="auth_firstName" value=${ auth_firstName }></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table cellspacing="0" cellpadding="2" style="padding:3px;">
                            <tr>
                                <td><span class="subDataCaptionFormat"> ${ _("Affiliation")}</span><span class="mandatoryField">&nbsp;*</span></td>
                                <td><span class="subDataCaptionFormat"> ${ _("Email")}</span><span class="mandatoryField">&nbsp;*</span></td>
                            </tr>
                            <tr>
                                <td><input type="text" size="28" name="auth_affiliation" value=${ auth_affiliation }></td>
                                <td><input type="text" size="30" name="auth_email" value=${ auth_email }></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table cellpacing="0" cellpadding="2">
                            <tr>
                                <td><span class="subDataCaptionFormat">${ _("Phone")}</span></td>
                            </tr>
                            <tr>
                                <td><input type="text" size="14" name="auth_phone" value=${ auth_phone }></td>
                                <td bgcolor="white" nowrap id="tdPrimaryPresenter${ auth_id }" class="${"tdSelected" if auth_speaker == 'checked' else "tdNotSelected"}" style="-moz-border-radius: 5px 5px 5px 5px; padding-right:6px; width:100%;">
                                    <input type="hidden" name="auth_primary" value="${ auth_id }">
                                    <input type="checkbox" id="primary_auth_speaker${ auth_id }" name="auth_speaker" value="${ auth_id }" ${ auth_speaker } onClick="switchPrimaryAuthorBackground('${ auth_id }')"> ${ _("This author will be also a <b>presenter</b>")}
                               </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <input type="hidden" name="auth_address" value="">
            </table>
        </td>

    </tr>
</table>
</td></tr>
<script>
    function switchPrimaryAuthorBackground(id) {
        if ($E('primary_auth_speaker'+id).get()) {
            $E('tdPrimaryPresenter'+id).dom.className = "tdSelected"
        }else {
            $E('tdPrimaryPresenter'+id).dom.className = "tdNotSelected"
        }
    }
</script>