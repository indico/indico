<table class="groupTable">
<tr>
  <td colspan="5"><div class="groupTitle">${ _("Access control")}</div></td>
</tr>
% if type == 'Home' :
<%include file="HomeAccessControlStatusFrame.tpl" args="setPrivacyURL=setPrivacyURL, privacy=privacy, locator = locator"/>
% else :
<%include file="AccessControlStatusFrame.tpl" args="parentName=parentName, privacy=privacy,
    parentPrivacy=parentPrivacy, statusColor = statusColor, parentStatusColor=parentStatusColor,
    locator=locator"/>
% endif
</table>

