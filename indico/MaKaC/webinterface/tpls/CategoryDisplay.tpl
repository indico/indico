
<%
import MaKaC.conference as conference
isRootCategory = categ == conference.CategoryManager().getRoot()
containsCategories = len(categ.getSubCategoryList()) > 0
%>
<div class="container">
<div class="categoryHeader">
<ul>
        % if not isRootCategory:
            <li><a href="${ urlHandlers.UHCategoryDisplay.getURL(categ.owner) }">${ _("Go to parent category") }</a>|</li>
        % endif
            % if categ.conferences:
                <li><a id="exportIcal${categ.getUniqueId()}" class="fakeLink exportIcal" data-id="${categ.getUniqueId()}">${ _("iCal export")}</a><span><%include file="CategoryICalExport.tpl" args="item=categ"/></span>|</li>

            % endif
        <li><a id="moreLink" class="dropDownMenu" href="#">${ _("View") }</a></li>
        % if allowCreateEvent:
            <li>|<a id="createEventLink" class="dropDownMenu" href="#">${ _("Create") }</a></li>
        % endif
        % if allowUserModif:
            <li style="font-weight: bold" >|<a id="manageLink" class="dropDownMenu highlight" href="#">${ _("Manage")}</a></li>
        % endif
        % if isLoggedIn and not isRootCategory:
            <li id="categFavorite"></li>
        % endif
</ul>
<h1 class="categoryTitle">
% if isRootCategory and containsCategories:
    ${ _("Main categories") }
% elif isRootCategory:
    ${ _("All events") }
% else:
    ${ name | remove_tags }
% endif
</h1>

% if isRootCategory and containsCategories:
<div class="categoryInfo">
    ${ _("Click on a category to start browsing through the hierarchy") }
</div>
% endif
% if description:
<div class="categoryInfo">
    ${ description }
</div>
% endif


% if managers:
    <div class="categoryManagers"><strong>${ _("Managers") }:</strong> ${ managers }</div>
% endif

</div>

<div>
${ contents }
</div>

</div>

<%
urlConference = urlHandlers.UHConferenceCreation.getURL(categ)
urlConference.addParam("event_type","conference")

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
    menuItems["todayEvents"] = {action: "${ urlHandlers.UHCategoryOverview.getURL(categ) }", display: "${ _("Today's events") }"};
    menuItems["weekEvents"] = {action: "${ urlHandlers.UHCategoryOverview.getWeekOverviewUrl(categ) }", display: "${ _("Week's events") }"};
    //menuItems["${ _("Month's events") }"] = "${ urlHandlers.UHCategoryOverview.getMonthOverviewUrl(categ) }";
    menuItems["calendar"] = {action: "${ urlHandlers.UHCalendar.getURL([categ]) }", display: '${ _("Calendar") }'};
    menuItems["categoryMap"] = {action: "${ urlHandlers.UHCategoryMap.getURL(categ) }", display: '${ _("Category map") }'};
    menuItems["categoryStatistics"] = {action: "${ urlHandlers.UHCategoryStatistics.getURL(categ) }", display: '${ _("Category statistics") }'};
    moreMenu = new PopupMenu(menuItems, [moreLink], 'categoryDisplayPopupList');
    var pos = moreLink.getAbsolutePosition();
    moreMenu.open(pos.x - 5, pos.y + moreLink.dom.offsetHeight + 3);
    return false;
});

</script>



% if allowCreateEvent:
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
    menuItems["lecture"] = {action: "${ urlLecture }", display: '${ _("Lecture") }'};
    menuItems["meeting"] = {action: "${ urlMeeting }", display: '${ _("Meeting") }'};
    menuItems["conference"] = {action: "${ urlConference }", display: '${ _("Conference") }' };

    createEventMenu2 = new PopupMenu(menuItems, [createEventLink2], 'categoryDisplayPopupList');
    var pos = createEventLink2.getAbsolutePosition();
    createEventMenu2.open(pos.x - 5, pos.y + createEventLink2.dom.offsetHeight + 2);
    return false;
});
</script>
% endif

% if allowUserModif:
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
    menuItems["editCategory"] = {action: "${ urlHandlers.UHCategoryModification.getURL(categ) }", display: '${ _("Edit category") }'};
    menuItems["addSubCategory"] = {action: "${ urlHandlers.UHCategoryCreation.getURL(categ) }", display: '${ _("Add subcategory") }' };
    manageMenu = new PopupMenu(menuItems, [manageLink], 'categoryDisplayPopupList');
    var pos = manageLink.getAbsolutePosition();
    manageMenu.open(pos.x - 5, pos.y + manageLink.dom.offsetHeight + 2);
    return false;
});
</script>
% endif

% if isLoggedIn:
    <script>
        var favoriteWidget = $('#categFavorite').favoriteButton({
            toggleFunc: function(favorite, promise) {
                indicoRequest('category.favorites.' + (favorite ? 'addCategory' : 'delCategory'), {
                    categId: '${ categ.getId() }'
                }, function(result, error) {
                    if(error) {
                        IndicoUtil.errorReport(error);
                        promise.reject();
                        return;
                    }

                    promise.resolve(favorite);
                });
            },
            favorite: ${ jsonEncode(categ in favoriteCategs) }
        });
    </script>
% endif