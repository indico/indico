<%
urlConference = urlHandlers.UHConferenceCreation.getURL(categ)
urlConference.addParam("event_type","conference")

urlLecture = urlHandlers.UHConferenceCreation.getURL(categ)
urlLecture.addParam("event_type","simple_event")

urlMeeting = urlHandlers.UHConferenceCreation.getURL(categ)
urlMeeting.addParam("event_type","meeting")

containsCategories = len(categ.getSubCategoryList()) > 0
%>

<div class="category-container">
    <div class="category-header">
        <div id="category-toolbar" class="toolbar right">

            % if isLoggedIn and not isRootCategory:
            <div id="categFavorite" class="group right">
                <a class="i-button fav-button icon-only icon-bookmark ${"enabled" if categ in favoriteCategs else ""}" href="#"></a>
            </div>
            % endif

            <div class="group right">
                % if not isRootCategory:
                <a class="i-button icon-arrow-up" href="${urlHandlers.UHCategoryDisplay.getURL(categ.owner)}">
                    Parent category
                </a>
                % endif

                % if categ.conferences:
                    <a id="exportIcal${categ.getUniqueId()}" class="i-button icon-calendar arrow exportIcal" data-id="${categ.getUniqueId()}"></a>
                    <span><%include file="CategoryICalExport.tpl" args="item=categ"/></span>
                % endif

                <a id="moreLink" class="i-button icon-eye arrow" data-toggle="dropdown"></a>
                <ul class="dropdown">
                    <li><a href="${urlHandlers.UHCategoryOverview.getURL(categ)}">${_("Today's events")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryOverview.getWeekOverviewUrl(categ)}">${_("Week's events")}</a></li>
                    <li><a href="${urlHandlers.UHCalendar.getURL([categ])}">${_("Calendar")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryMap.getURL(categ)}">${_("Category map")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryStatistics.getURL(categ)}">${_("Category statistics")}</a></li>
                </ul>
                <a id="createEventLink" class="i-button icon-plus arrow" data-toggle="dropdown"></a>
                <ul class="dropdown">
                    <li><a href="${urlLecture}">${_("Lecture")}</a></li>
                    <li><a href="${urlMeeting}">${_("Meeting")}</a></li>
                    <li><a href="${urlConference}">${_("Conference")}</a></li>
                </ul>

                % if allowUserModif:
                <a id="manageLink" class="i-button icon-edit arrow" data-toggle="dropdown"></a>
                <ul class="dropdown">
                    <li><a href="${urlHandlers.UHCategoryModification.getURL(categ)}">${_("Edit category")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryCreation.getURL(categ)}">${_("Add subcategory")}</a></li>
                </ul>
                % endif
            </div>
        </div>

        <h1 class="category-title ${"sidebar-padding" if isRootCategory or materials or managers else ""}">
        % if isRootCategory and containsCategories:
            ${ _("Main categories") }
        % elif isRootCategory:
            ${ _("All events") }
        % else:
            ${ name | remove_tags }
        % endif
        </h1>
    </div>

    % if isRootCategory or materials or managers:
    <div class="category-sidebar">
        % if isRootCategory:
            % if isNewsActive:
                <h2 class="icon-bullhorn">${_("News")}</h2>
                <%include file="WelcomeHeader.tpl" args="tz = timezone"/>
            % endif
            % if upcomingEvents:
                <h2 class="icon-time">${_("Upcoming events")}</h2>
                    ${upcomingEvents}
            % endif
        % else:
            % if materials:
                <h2 class="icon-material-download">${ _("Files") }</h2>
                <ul id="manager-list">
                % for mat, url in materials:
                    <li><a href="${url}">${mat.getTitle()}</a></li>
                % endfor
                </ul>
            % endif
            % if managers:
                <h2 class="icon-medal">${ _("Managers") }</h2>
                <ul id="manager-list">
                % for type, mgr_name in managers:
                    <li class="${type}">${mgr_name}</li>
                % endfor
                </ul>
            % endif
        % endif
    </div>
    % endif

    <div class="clearfix category-content">
        <div class="category-info">

        % if isRootCategory:
            ${_("Welcome to Indico. The Indico tool allows you to manage complex conferences, workshops and meetings.<br/> In order to start browsing, please select one of the categories below.")}
        % elif description:
            ${description}
        % endif
        </div>

        <div>
            ${ contents }
        </div>
    </div>
</div>

<script>
$(document).ready(function(){

    $("#category-toolbar").dropdown();

    $(".category-sidebar").css('height', $(".category-container").height());

    var PROTECTION_TEXT = {
            'domain': $T("This category is protected by domain: "),
            'restricted': $T("This category is restricted to some users")
        };

    // Make category entries fully clickable (wrap in <a>)
    $('.category-list li').each(function() {
         return $(this).children().wrapAll(
             $('<a class="invisible-block"/>').attr('href', $(this).find('a').attr('href'))
         );
    });

    $('.protection').qtip({
        content: {
            text: function() {
                var type = $(this).data('type');
                var domains = ($(this).data('domain') || []).join(", ");
                return PROTECTION_TEXT[type] + (type == "domain" ? domains : "");
            }
        },
        position: {
            my: 'top center',
            at: 'bottom center'
        }
    })
});
</script>

% if isLoggedIn:
    <script>
    $(document).ready(function(){
        $('.i-button.fav-button').click(function() {
            $(this).toggleClass('enabled');
            indicoRequest('category.favorites.' + ($(this).hasClass("enabled") ? 'addCategory' : 'delCategory'), {
                categId: '${ categ.getId() }'
            }, function(result, error) {
                if(error) {
                    IndicoUtil.errorReport(error);
                    return;
                }
            });
        });
    });
    </script>
% endif