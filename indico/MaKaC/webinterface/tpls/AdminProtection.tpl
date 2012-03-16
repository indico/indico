<div class="groupTitle">${ _("Protection")}</div>

<table class="groupTable">
<tr>
  <td>
    <table width="100%" border="0">
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Protected information disclaimer")}</span>
        </td>
        <td>
            <div class="blacktext" id="inPlaceEditDisclaimerProtected">${protectionDisclaimerProtected}</div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Restricted information disclaimer")}</span>
        </td>
        <td>
            <div class="blacktext" id="inPlaceEditDisclaimerRestricted">${protectionDisclaimerRestricted}</div>
        </td>
    </tr>
    </table>
  </td>
</tr>
</table>

<script type="text/javascript">
$E('inPlaceEditDisclaimerProtected').set(new ParsedRichTextInlineEditWidget('admin.protection.editProtectionDisclaimerProtected', {}, '${protectionDisclaimerProtected}', null, null, "${_('No info')}").draw());
$E('inPlaceEditDisclaimerRestricted').set(new ParsedRichTextInlineEditWidget('admin.protection.editProtectionDisclaimerRestricted', {}, '${protectionDisclaimerRestricted}', null, null, "${_('No info')}").draw());

</script>
