<% includeTpl('Announcement') %>

<div class="pageHeader pageHeaderMainPage clearfix">
        <% includeTpl('SessionBar') %>

        <!--
            set fixed height on anchor to assure that the height is
            corrected if the image cannot be retrieved (i.e. https problems) -->
        <a style="min-height: 66px;" href="<%= urlHandlers.UHWelcome.getURL() %>">
            <img class="headerLogo" src="<%= imgLogo %>" />
        </a>

    <div class="headerAboutIndico">
        <%= _("Burotel, Desk booking service") %>
    </div>
    <% if len(adminItemList) >= 1: %>
    <div class="globalMenu">
        <ul>

                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHRoomBookingWelcome.getURL() %>"><%= _("Room booking") %></a></li>
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= adminItemList[0]['url'] %>"><%= adminItemList[0]['text'] %></a></li>
        </ul>
    </div>
   <% end %>
</div>
