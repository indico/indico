<%!
from MaKaC.modules.base import ModulesHolder
newsModule = ModulesHolder().getById("news")
newsList = newsModule.getNewsItemsList()
%>

<ul>
    <% for newItem in newsList[:3]: %>
        <li><a href="<%= urlHandlers.UHIndicoNews.getURL()%>"><%= newItem.getTitle() %></a><em><%= _('Posted on') %>&nbsp;<%= formatDateTime(newItem.getCreationDate()) %></em></li>
    <% end %>
    <% end %>
    <li><a href="<%= urlHandlers.UHIndicoNews.getURL()%>" class="subLink"><%= _("View news history") %></a></li>
</ul>
