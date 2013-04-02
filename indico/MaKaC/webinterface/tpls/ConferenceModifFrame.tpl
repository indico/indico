<%
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>

<div class="banner">

    <div style="float: right; height: 20px; line-height: 20px;padding:0px;" class="eventModifButtonBar">
        <div style="border-bottom:1px solid #AAA;"><span class="eventActionsToolBarLabel"><strong>Event</strong> actions</span></div>
        <div class="eventActionsToolBarButtons">
          <a style="vertical-align: middle;" href="${ urlHandlers.UHConfClone.getURL(conf) }">
              ${ _("Clone") }<div class="leftCorner"></div>
          </a>
    % if not conf.isClosed():
          <a style="vertical-align: middle;" href="${ urlHandlers.UHConferenceClose.getURL(conf) }">
              ${ _("Lock") }<div class="leftCorner"></div>
          </a>
    % else:
          <a style="vertical-align: middle;" href="${ urlHandlers.UHConferenceOpen.getURL(conf) }">
              ${ _("Unlock") }<div class="leftCorner"></div>
          </a>
    % endif
          <div class="separator"></div>
          <a class="eventModifSpecial" style="vertical-align: middle;" href="${ urlHandlers.UHConferenceDisplay.getURL( conf ) }">
              ${ _("Switch to event page") }<div class="leftCorner"></div>
          </a>
        </div>
    </div>

    <a href="${ UHConferenceModification.getURL(conf) }">
        <span class="bannerTitle bannerTitle_0">
            ${ conf.getTitle() | remove_tags } &nbsp;<span style="font-size: 0.8em; font-style: italic;">
            % if startDate == endDate:
                ${ startDate }
            % else:
                ${ startDate } - ${ endDate }
            % endif
            </span>
        </span>
    </a>
    <div class="banner_creator">
        % if conf.getCreator():
            ${ _("Created by ")}
            % if conf.getCreator().getStraightFullName().strip():
                ${ ("%s -") % conf.getCreator().getStraightFullName().strip()}
            % endif
            ${conf.getCreator().getEmail()}
        % endif
    </div>

</div>

<table cellpadding="0" cellspacing="0" style="width:100%">
    <tbody>
        <tr>
            <td style="vertical-align: top; width:200px">${ sideMenu }</td>
            <td style="vertical-align: top">
                <div class="body" style="padding:20px;">
                    ${ body }
                </div>
            </td>
        </tr>
    </tbody>
</table>
