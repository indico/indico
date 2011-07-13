
<%
import MaKaC.conference as conference
isRootCategory = categ == conference.CategoryManager().getRoot()
containsCategories = len(categ.getSubCategoryList()) > 0
%>
<div class="container">
<div class="categoryHeader">
<ul>
        <% if not isRootCategory: %>
            <li><a href="<%= urlHandlers.UHCategoryDisplay.getURL(categ.owner) %>"><%= _("Go to parent category") %></a>|</li>
        <% end %>
            <% if categ.conferences: %>
                <li><a href="<%= urlHandlers.UHCategoryToiCal.getURL(categ) %>"><%= _("iCal export")%></a>|</li>
            <% end %>
        <li><a id="moreLink" class="dropDownMenu" href="#"><%= _("View") %></a></li>
        <% if allowCreateEvent: %>
            <li>|<a id="createEventLink" class="dropDownMenu" href="#"><%= _("Create") %></a></li>
        <% end %>
        <% if allowUserModif: %>
            <li style="font-weight: bold" >|<a id="manageLink" class="dropDownMenu highlight" href="#"><%= _("Manage")%></a></li>
        <% end %>
</ul>
<h1 class="categoryTitle">
<% if isRootCategory and containsCategories: %>
    <%= _("Main categories") %>
<% end %>
<% elif isRootCategory: %>
    <%= _("All events") %>
<% end %>
<% else: %>
    <%= name %>
<% end %>
</h1>

<% if isRootCategory and containsCategories: %>
<div class="categoryInfo">
    <%= _("Click on a category to start browsing through the hierarchy") %>
</div>
<% end %>
<% if description: %>
<div class="categoryInfo">
    <%= description %>
</div>
<% end %>


<% if managers: %>
	<div class="categoryManagers"><strong><%= _("Managers") %>:</strong> <%= managers %></div>
<% end %>

<!--
<% if taskList: %>
<h2 class="subtitle">
	<%= taskList %>
</h2>
<% end %>
-->
</div>

<div>
<%= contents %>
</div>

</div>

<%
urlConference = urlHandlers.UHConferenceCreation.getURL(categ)
urlConference.addParam("event_type","default")

urlLecture = urlHandlers.UHConferenceCreation.getURL(categ)
urlLecture.addParam("event_type","simple_event")

urlMeeting = urlHandlers.UHConferenceCreation.getURL(categ)
urlMeeting.addParam("event_type","meeting")
%>

<script type="text/javascript">
var moreLink = $E('moreLink');
var moreMenu = null;
moreLink.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (moreMenu != null && moreMenu.isOpen()) {
        moreMenu.close();
        moreMenu = null;
        return;
    }

    var menuItems = {};
    menuItems["<%= _("Today's events") %>"] = "<%= urlHandlers.UHCategoryOverview.getURL(categ) %>";
    menuItems['<%= _("Calendar") %>'] = "<%= urlHandlers.UHCalendar.getURL([categ]) %>";
    menuItems['<%= _("Category map") %>'] = "<%= urlHandlers.UHCategoryMap.getURL(categ) %>";
    menuItems['<%= _("Category statistics") %>'] = "<%= urlHandlers.UHCategoryStatistics.getURL(categ) %>";
    moreMenu = new PopupMenu(menuItems, [moreLink], 'categoryDisplayPopupList');
    var pos = moreLink.getAbsolutePosition();
    moreMenu.open(pos.x - 5, pos.y + moreLink.dom.offsetHeight + 3);
    return false;
});
</script>



<% if allowCreateEvent: %>
<script type="text/javascript">
var createEventLink2 = $E('createEventLink');
var createEventMenu2 = null;
createEventLink2.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (createEventMenu2 != null && createEventMenu2.isOpen()) {
        createEventMenu2.close();
        createEventMenu2 = null;
        return;
    }

    var menuItems = {};
    menuItems['<%= _("Lecture") %>'] = "<%= urlLecture %>";
    menuItems['<%= _("Meeting") %>'] = "<%= urlMeeting %>";
    menuItems['<%= _("Conference") %>'] = "<%= urlConference %>";

    createEventMenu2 = new PopupMenu(menuItems, [createEventLink2], 'categoryDisplayPopupList');
    var pos = createEventLink2.getAbsolutePosition();
    createEventMenu2.open(pos.x - 5, pos.y + createEventLink2.dom.offsetHeight + 2);
    return false;
});
</script>
<% end %>

<% if allowUserModif: %>
<script type="text/javascript">
var manageLink = $E('manageLink');
var manageMenu = null;
manageLink.observeClick(function(e) {
    // Close the menu if clicking the link when menu is open
    if (manageMenu != null && manageMenu.isOpen()) {
        manageMenu.close();
        manageMenu = null;
        return;
    }

    var menuItems = {};
    menuItems['<%= _("Edit category") %>'] = "<%= urlHandlers.UHCategoryModification.getURL(categ) %>";
    menuItems['<%= _("Add subcategory") %>'] = "<%= urlHandlers.UHCategoryCreation.getURL(categ) %>";
    manageMenu = new PopupMenu(menuItems, [manageLink], 'categoryDisplayPopupList');
    var pos = manageLink.getAbsolutePosition();
    manageMenu.open(pos.x - 5, pos.y + manageLink.dom.offsetHeight + 2);
    return false;
});
</script>
<% end %>
