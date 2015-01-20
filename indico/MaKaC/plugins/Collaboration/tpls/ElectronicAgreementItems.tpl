<%page args="spkId, spkName, status, contribId, reqType, enabled, canModify"/>
<% spkWrapper = manager.getSpeakerWrapperByUniqueId("%s.%s" % (contribId, spkId))
contribution = conf.getContributionById(contribId)  %>

<%
   cssColor = {SpeakerStatusEnum.NOEMAIL:"#881122",
               SpeakerStatusEnum.NOTSIGNED:"#881122",
               SpeakerStatusEnum.REFUSED: "#881122",
               SpeakerStatusEnum.PENDING: "#FF7F00",
               SpeakerStatusEnum.SIGNED: "#118822",
               SpeakerStatusEnum.FROMFILE: "#118822"}[spkWrapper.getStatus()]
%>

<tr class="speakerLine">
  <td valign="middle" align="right" width="3%">
    <input ${'disabled="disabled"' if not enabled else ''} id="${spkWrapper.getUniqueId()}" class="speakerCheck" type="checkbox" name="cont" class="speakerCheckbox" />
  </td>
  <td class="CRLabstractLeftDataCell" nowrap>
    ${spkWrapper.getObject().getFullName()}
  </td>
  <td class="CRLabstractLeftDataCell" nowrap>
    <img style="cursor:pointer;margin-right:5px;"
         src="${systemIcon('edit')}" alt="${'Edit email' | _}" title="${'Edit email' | _}"
         onclick="new EditSpeakerEmail('${conf.getType()}','${spkWrapper.getObject().getFullName()}', '${spkId}','${spkWrapper.getObject().getEmail()}', '${conf.getId()}', '${contribId}').open()" />
    ${spkWrapper.getObject().getEmail()}
  </td>
  <td class="CRLabstractLeftDataCell" nowrap  style="color: ${cssColor};">
    ${STATUS_STRING[spkWrapper.getStatus()]}
    % if spkWrapper.getStatus() == SpeakerStatusEnum.REFUSED:
        <img id="reject${spkWrapper.getUniqueId()}" class="reject" name="${spkWrapper.getRejectReason()}" alt="Tooltip" src="${systemIcon('help')}" style="vertical-align:text-bottom; border:None;" />
    % endif
  </td>
  <td class="CRLabstractLeftDataCell" nowrap>
   <% reqTypeText = {"recording": "REC",
                     "webcast": "WEBC",
                     "both": "REC/WEBC",
                     "NA": "NA"}[spkWrapper.getRequestType()] %>
   ${reqTypeText}
  </td>
  <td class="CRLabstractLeftDataCell">
<%
if contribution is None:
    contLink = urlHandlers.UHConferenceDisplay.getURL(conf)
elif isAdminUser or manager.isVideoServicesManager(user):
    contLink = urlHandlers.UHContributionModification.getURL(contribution)
else:
    contLink = urlHandlers.UHContributionDisplay.getURL(contribution)
%>
    <% contTitle = contribution.getTitle() if contribution else conf.getTitle() %>
    <a href = "${contLink}" id='name${spkWrapper.getUniqueId()}' class='contName' name="${contTitle}">${truncateTitle(contTitle, 10)}</a>
  </td>

  <td class="CRLabstractLeftDataCell" nowrap>
    % if canModify:
        <a href="#" onclick="new UploadElectronicAgreementPopup('${conf.getId()}','${spkWrapper.getUniqueId()}','${collaborationUrlHandlers.UHCollaborationUploadElectronicAgreement.getURL(conf)}').open();return false;" id="upload${spkWrapper.getUniqueId()}">${_("Upload")}</a>
    % else:
        <span class="noUploadRights">${_("Upload")}</span>
    % endif
    % if spkWrapper.getLocalFile():
      <a href="${collaborationUrlHandlers.UHCollaborationElectronicAgreementGetFile.getURL(conf, spkWrapper.getUniqueId())}">
        <img style="cursor:pointer;margin-right:5px;" src="${systemIcon('pdf')}"
             alt="${'Paper Agreement' | _}" title="${'Paper Agreement'}" />
      </a>
    % endif
</td>
