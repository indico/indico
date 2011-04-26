<td class="ttManagementBlock" style="vertical-align: top; background-color: ${ bgcolor };" rowspan="${ rowspan }" width="${ width }%" ${ colspan } >

<div style="height: 20px; width: 100%;">
  <div style="width: 60px; float: right;" class="nonLinked">
    <div class="ttModifIcon" style="margin: 3px;" onclick="return contributionMenu($E(this), '${ urlHandlers.UHContributionModification.getURL(self_._contrib, day=days) }', '${ self_._contrib.id }','${ self_._contrib.getConference().id }', '${ delURL }', '${ relocateURL }');">
    </div>
    <div style="margin-top: 3px;">
      <a href="${ moveUpURL }"><img src="${ Config.getInstance().getSystemIconURL("upArrow") }" border="0" alt="${ _("move entry before the previous one")}"></a>
      <a href="${ moveDownURL }"><img src="${ Config.getInstance().getSystemIconURL("downArrow") }" border="0" alt="${ _("move entry after the next one")}"></a>
    </div>
  </div>
</div>

<div style="overflow: show; margin-left: 10px; margin-bottom: 5px; text-align: left;">
    ${"<p>"+ header +"</p>" if 'header' in vars() else ""}
    <%from MaKaC.common.TemplateExec import truncateTitle %>
    <p style="align: left; font-size: 12pt; margin-top: 5px; margin-bottom: 2px;">${ self_.htmlText(truncateTitle(self_._contrib.getTitle(), 40)) }</p>
    <small class="ttMBlockExtraInfo">
    ${ self_.htmlText(place) }
           ${ self_.htmlText(self_._contrib.getAdjustedStartDate().strftime("%H:%M")) }-${ self_.htmlText(self_._contrib.getAdjustedEndDate().strftime("%H:%M")) }
    </small>
    ${ footer  if 'footer' in vars() else ""}

    % if subCont != []:
    <ul style="list-style: inside; border-top: 1px solid #CCCCCC; padding-left: 0px;">
        % for sub in subCont:
          <li style="display: block; padding-left: 30px; padding-bottom: 15px; border-bottom: 1px solid #CCCCCC;">
              <div style="overflow: auto;">
                  <ul class="slotHorizontalMenu" style="float:right;">
                    <li><a href="${ urlHandlers.UHSubContributionModification.getURL(sub) }">Edit</a></li>
                    <li><a href="#" onclick="if (confirm('${ _("Delete subcontribution") } ${ escapeAttrVal(sub.getTitle()) }?')) {IndicoUI.Services.deleteSubContribution('${ self_._contrib.getConference().getId() }', '${ self_._contrib.getId() }', '${ sub.getId() }');} return false;">Delete</a></li>
                  </ul>
                  <div style="overflow:visible; margin-top: 15px;">${ truncateTitle(sub.getTitle(), 40) }</span>
              </div>

          </li>
        % endfor
    </ul>
    % endif

</div>
</td>
