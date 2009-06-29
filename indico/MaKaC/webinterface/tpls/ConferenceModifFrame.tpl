<%!
from MaKaC.webinterface.urlHandlers import UHConferenceModification
%>
<%# includeTpl('BannerModif') %>

<div class="banner">
    <span class="banner_creator">
        <% if conf.getCreator(): %>
            <%= _("Created by")%>
            <strong><%= conf.getCreator().getFullName() %></strong><br>         
        <% end %>
        
    </span>
    <a href="<%= UHConferenceModification.getURL(conf) %>">
        <span class="bannerTitle bannerTitle_0">
            <%= conf.getTitle() %> &nbsp;<span style="font-size: 0.8em; font-style: italic;"><%= date %></span>
        </span>
    </a>


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