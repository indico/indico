<% declareTemplate(newTemplateStyle = True) %>

<% includeTpl('InterfaceSwitcher') %>
<% includeTpl('Announcement') %>

<div class="pageHeader pageHeaderMainPage clearfix">
        <% includeTpl('SessionBar') %>

        <% if searchBox != '': %>
            <%= searchBox %>
        <% end %>

        <!--
            set fixed height on anchor to assure that the height is
            corrected if the image cannot be retrieved (i.e. https problems) -->
        <a style="display: block; min-height: 66px;" href="<%= urlHandlers.UHWelcome.getURL() %>">
            <img class="headerLogo" src="<%= imgLogo %>" />
        </a>

		<% if isFrontPage: %>
		    <div class="headerAboutIndico">
		        <%= _("The Indico tool allows you to manage complex conferences, workshops and meetings.") %>
		    </div>
		<% end %>

    <div class="globalMenu">
        <ul>
            <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHWelcome.getURL() %>"><%= _("Home") %></a></li>
        	<li id="createEventMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu"><%= _("Create event") %></span></li>

            <% if roomBooking: %>
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHRoomBookingWelcome.getURL() %>"><%= _("Room booking") %></a></li>
            <% end %>

            <% if len(adminItemList) == 1: %>
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= adminItemList[0]['url'] %>"><%= adminItemList[0]['text'] %></a></li>
            <% end %>
            <% elif len(adminItemList) > 1: %>
                <li id="administrationMenu" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu"><%= _("Administration") %></span></li>
            <% end %>

            <% if currentUser: %>
                <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHUserDetails.getURL(currentUser) %>"><%= _("My profile") %></a></li>
            <% end %>

            <li id="helpMenu"  onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><span class="dropDownMenu"><%= _("Help") %></span></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHContact.getURL() %>">Contact</a></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHCategoryMap.getURL(categId=0) %>">Site Map</a></li>
            <li style="display: none;" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''"><a href="<%= urlHandlers.UHAbout.getURL() %>">About Indico</a></li>

            <li onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''" style="display: none;"><a href="urlHandlers.UHGetUserEventPage.getURL()"><%= _("My Indico") %></a></li>
        </ul>
    </div>
</div>

<%
urlConference = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlConference.addParam("event_type","default")

urlLecture = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlLecture.addParam("event_type","simple_event")

urlMeeting = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlMeeting.addParam("event_type","meeting")
%>

<script type="text/javascript">
var createEventMenu = $E('createEventMenu');
createEventMenu.observeClick(function(e) {
    var menuItems = {};

    menuItems['<%= _("Create lecture") %>'] = "<%= urlLecture %>";
    menuItems['<%= _("Create meeting") %>'] = "<%= urlMeeting %>";
    menuItems['<%= _("Create conference") %>'] = "<%= urlConference %>";

    var menu = new PopupMenu(menuItems, [createEventMenu], "globalMenuPopupList");
    var pos = createEventMenu.getAbsolutePosition();
    menu.open(pos.x, pos.y + 30);
    return false;
});

<% if len(adminItemList) > 1: %>

    var administrationMenu = $E('administrationMenu');
    administrationMenu.observeClick(function(e) {
        var menuItems = {};

        <% for item in adminItemList: %>
        menuItems["<%= item['text']%>"] = "<%= item['url'] %>"
        <% end %>
        var menu = new PopupMenu(menuItems, [administrationMenu], "globalMenuPopupList");
        var pos = administrationMenu.getAbsolutePosition();
        menu.open(pos.x, pos.y + 30);
        return false;
    });

<% end %>

var helpMenu = $E('helpMenu');
helpMenu.observeClick(function(e) {
    var menuItems = {};

    menuItems['<%= _("Indico help") %>'] = "<%= urlHandlers.UHConferenceHelp.getURL() %>";
    menuItems['<%= _("About Indico") %>'] = "<%= urlHandlers.UHAbout.getURL() %>";
    menuItems['<%= _("Contact") %>'] = "<%= urlHandlers.UHContact.getURL() %>";

    var menu = new PopupMenu(menuItems, [helpMenu], "globalMenuPopupList");
    var pos = helpMenu.getAbsolutePosition();
    menu.open(pos.x, pos.y + 30);
    return false;
});
</script>


