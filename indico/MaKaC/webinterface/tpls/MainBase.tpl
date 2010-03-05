<% declareTemplate(newTemplateStyle=True) %>

<% if not isFrontPage and navigation: %>
    <%= navigation %>
<% end %>
<% else: %>
    <div class="mainNoBreadcrumb">
    </div>
<% end %>

<div class="clearfix">
    <% if isRoomBooking: %>
        <% if sideMenu: %>
            <div class="emptyVerticalGap"></div>
        <% end%>
        <table border="0" cellSpacing="0" cellPadding="0">
            <tr>
                <% if sideMenu: %>
                <td style="vertical-align: top;">
    		        <%= sideMenu %>
                </td>
                <% end %>
                <td style="vertical-align: top; width: 100%;">
                	<div class="body clearfix <% if sideMenu: %>bodyWithSideMenu<% end %> <% if isFrontPage: %>bodyWithSideBar<% end %>" style="margin-left:0px;">
                        <%= body %>
                    </div>
                </td>
            </tr>
        </table>

    <% end %>
    <% else: %>

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
    <% end %>
</div>
