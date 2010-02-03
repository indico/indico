<%!
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>
<%# includeTpl('BannerModif') %>

<div class="banner">

    <% if not conf.isClosed(): %>
        <div style="float: right; height: 20px; line-height: 20px;" class="eventModifButtonBar">
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConfClone.getURL(conf) %>">
              <%= _("Clone") %><div class="leftCorner"></div>
          </a>
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConferenceClose.getURL(conf) %>">
              <%= _("Lock") %><div class="leftCorner"></div>
          </a>
          <a style="vertical-align: middle;" href="<%= urlHandlers.UHConfDeletion.getURL(conf) %>">
              <%= _("Delete") %><div class="leftCorner"></div>
          </a>
        </div>
    <% end %>

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