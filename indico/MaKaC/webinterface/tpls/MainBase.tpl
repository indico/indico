<% if not isFrontPage and navigation: %>
    <%= navigation %>
<% end %>
<% else: %>
    <div class="mainNoBreadcrumb">
    </div>
<% end %>

<div class="clearfix">
	<% if sideMenu: %>
        <div class="emptyVerticalGap"></div>
		<%= sideMenu %>
	<% end %>
    <% if isFrontPage: %>
        <div class="frontPageSideBarContainer">
            <div class="sideBar">
                <div class="leftCorner"></div>
                <div class="rightCorner"></div>
                <div class="content">
                <h1><%= _("News") %></h1>
                    <% includeTpl('WelcomeHeader', tz = timezone) %>
                <h1><%= _("Upcoming events") %></h1>
                    <%= upcomingEvents %>
                </div>
            </div>
        </div>
    <% end %>
	<div class="body clearfix <% if sideMenu: %>bodyWithSideMenu<% end %> <% if isFrontPage: %>bodyWithSideBar<% end %>">
        <%= body %>
    </div>
</div>
