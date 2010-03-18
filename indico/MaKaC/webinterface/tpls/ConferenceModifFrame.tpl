<%!
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>
<%# includeTpl('BannerModif') %>

<div class="banner">

        <div style="float: right; height: 20px; line-height: 20px;" class="eventModifButtonBar">
    <% if not conf.isClosed(): %>
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConfClone.getURL(conf) %>">
              <%= _("Clone") %><div class="leftCorner"></div>
          </a>
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConferenceClose.getURL(conf) %>">
              <%= _("Lock") %><div class="leftCorner"></div>
          </a>
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConfDeletion.getURL(conf) %>">
              <%= _("Delete") %><div class="leftCorner"></div>
          </a>
          <div class="separator"></div>
    <% end %>

          <a class="eventModifSpecial" style="vertical-align: middle;" href="<%= urlHandlers.UHConferenceDisplay.getURL( conf ) %>">
              <%= _("Switch to event page") %><div class="leftCorner"></div>
          </a>

        </div>

    <a href="<%= UHConferenceModification.getURL(conf) %>">
        <span class="bannerTitle bannerTitle_0">
            <%= conf.getTitle() %> &nbsp;<span style="font-size: 0.8em; font-style: italic;"><%= date %></span>
        </span>
    </a>
    <div class="banner_creator">
        <% if conf.getCreator(): %>
            <%= _("Created by")%>&nbsp;<%= conf.getCreator().getStraightFullName() %>
        <% end %>

    </div>

</div>

<table cellpadding="0" cellspacing="0" style="width:100%%">
    <tbody>
        <tr>
            <td style="vertical-align: top; width:200px">%(sideMenu)s</td>
            <td style="vertical-align: top">
                <div class="body" style="padding:20px;">
                    %(body)s
                </div>
            </td>
        </tr>
    </tbody>
</table>