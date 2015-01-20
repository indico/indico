<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.webinterface.linking as linking %>

<div id="buttonBar" class="subContributionButtonBar">
    % if SubContrib.canModify(accessWrapper):
    <a href="${str(urlHandlers.UHSubContributionModification.getURL(SubContrib))}" style="font-weight: bold">${_("Edit")}</a>
    % endif
</div>

<h1 class="subContributionTitle">
    ${SubContrib.getTitle()}
</h1>
<div>
    <div class="subContributionMainContent">
        <div class="subContributionInformation">
            <%block name="speakers">
            </%block>
            <div class="subContributionHeader">
                <div><span style="font-weight:bold">${_("Duration")}: </span>${duration}</div>
                % if SubContrib.getParent() != None:
                    <div>
                        <span style="font-weight:bold">${_("Included in contribution")}: </span>
                        <a class ="lightGreyLink" href="${str(urlHandlers.UHContributionDisplay.getURL(SubContrib.getParent()))}" >
                            ${SubContrib.getParent().getTitle()}
                        </a>
                    </div>
                % endif
                <%block name="reportNumber">
                </%block>
            </div>
        </div>
        <div class="subContributionDetail">
            <div class="subContributionSection">
                <h2 class="subContributionSectionTitle">${_("Description")}</h2>
                <div class="subContributionSectionContent">${SubContrib.getDescription()}</div>
            </div>
        </div>
    </div>
    <div class="subContributionRightPanel">
        <% location = SubContrib.getLocation() %>
        <% room = SubContrib.getRoom() %>
        % if location or room:
        <div class="subContributionRightPanelSection">
            <h2 class="subContributionSectionTitle">${_("Place")}</h2>
            % if location:
                <div><span style="font-weight:bold">${_("Location")}: </span>${location.getName()}</div>
                % if location.getAddress() is not None and location.getAddress()!="":
                <div><span style="font-weight:bold">${_("Address")}: </span>${location.getAddress()}</div>
                % endif
            % endif
            % if room:
                <div><span style="font-weight:bold">${_("Room")}: </span>${linking.RoomLinker().getHTMLLink(room,location)}</div>
            % endif
        </div>
        % endif
        % if SubContrib.getAllMaterialList():
            <div class="subContributionRightPanelSection">
                <h2 class="subContributionSectionTitle">${_("Material")}</h2>
               % if (SubContrib.canUserSubmit(self_._aw.getUser()) or SubContrib.canModify(self_._aw)) and not isWithdrawn:
                <div style="float:right; line-height: 17px">
                    <a class="fakeLink" id="manageMaterial">Edit files</a>
                </div>
                % endif
                <ul>
                % for material in SubContrib.getAllMaterialList():
                    <li><a href="${urlHandlers.UHMaterialDisplay.getURL(material)}"  class="titleWithLink">
                        ${material.getTitle()}
                        </a>
                     <ul class="subList">
                     % for resource in material.getResourceList():
                     <li><a href="${urlHandlers.UHFileAccess.getURL(resource)}" target="_blank">
                        ${resource.getName()}
                        </a>
                        </li>
                     % endfor
                     </ul>
                     </li>
                % endfor
                </ul>
            </div>
        % endif
    </div>
</div>
<script type="text/javascript">
    $("#manageMaterial").click(function(){
        IndicoUI.Dialogs.Material.editor('${SubContrib.getConference().getOwner().getId()}', '${SubContrib.getConference().getId()}',
            '${SubContrib.getSession().getId() if SubContrib.getSession() else ""}','${SubContrib.getParent().getId()}','${SubContrib.getId()}',
                ${jsonEncode(SubContrib.getAccessController().isProtected())}, ${jsonEncode(SubContrib.getMaterialRegistry().getMaterialList(SubContrib.getConference()))}, ${'Indico.Urls.UploadAction.subcontribution'}, true);
     });
</script>
