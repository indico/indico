<%!
from MaKaC.webinterface.urlHandlers import UHHelper
from MaKaC.conference import Category
from MaKaC.conference import Track
from MaKaC.review import Abstract
from MaKaC.common import Configuration

l = []

while target != None:
    if type(target) == Category:
        name = target.getName()
    else:
        name = target.getTitle()

    if isModif:
        url = UHHelper.getModifUH(type(target)).getURL(target)
    else:
        if actionType:
            catType = actionType
        else:
            catType = ''
        url = UHHelper.getDisplayUH(type(target), catType).getURL(target)

    l.append( (name, url) )

    if type(target) != Abstract:
        target = target.getOwner()
    else:
        if track:
            if isModif:
                url = UHHelper.getModifUH(Track).getURL(track)
            else:
                url = UHHelper.getDisplayUH(Track).getURL(track)
            l.append( (track.getTitle(), url) )
        target = target.getOwner().getOwner()


l.reverse()

arrowImage = systemIcon( "breadcrumb_arrow.png" )

%>

<div class="mainBreadcrumb" <% if bgColor: %>style="background-color: <%= bgColor %>;" <% end %>>
<span class="path">
    <% for i in range (0, len(l)): %>
        <% if i > 0: %>
            <img src="<%= arrowImage %>" />
        <% end %>
        <% name, url = l[i] %>
        <a href="<%= url %>">
            <%= truncateTitle(name, 40) %>
        </a>
    <% end %>

    <% for i in range(0, len(appendPath)): %>
        <% object = appendPath[i] %>

        <img src="<%= arrowImage %>" />

        <a href="<%= object["url"] %>"><%= object["title"] %></a>
    <% end %>

</span>
</div>