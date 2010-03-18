<%!
from MaKaC.modules.base import ModulesHolder
from MaKaC.common.timezoneUtils import DisplayTZ
newsModule = ModulesHolder().getById("news")
newsList = newsModule.getNewsItemsList()
%>

<ul>
    <% for newItem in newsList[:2]: %>
        <li>
            <a href="<%= urlHandlers.UHIndicoNews.getURL()%>">
                <%= newItem.getTitle() %>
            </a>
            <em><%= _('Posted on') %>&nbsp;<%= formatDate(newItem.getAdjustedCreationDate(tz)) %></em>
        </li>
    <% end %>
    <% end %>
    <li><a href="<%= urlHandlers.UHIndicoNews.getURL()%>" class="subLink"><%= _("View news history") %></a></li>
</ul>
