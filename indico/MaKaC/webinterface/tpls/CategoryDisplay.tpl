<%
urlConference = urlHandlers.UHConferenceCreation.getURL(categ)
urlConference.addParam("event_type","conference")

urlLecture = urlHandlers.UHConferenceCreation.getURL(categ)
urlLecture.addParam("event_type", "lecture")

urlMeeting = urlHandlers.UHConferenceCreation.getURL(categ)
urlMeeting.addParam("event_type","meeting")

containsCategories = len(categ.getSubCategoryList()) > 0
from MaKaC.conference import Link
from MaKaC.webinterface.general import strfFileSize
%>

<div class="category-container">
    <div class="category-header">
        <div id="category-toolbar" class="toolbar right">
            <div class="group">
                % if not isRootCategory:
                <a class="i-button icon-arrow-up" href="${urlHandlers.UHCategoryDisplay.getURL(categ.owner)}">
                    Parent category
                </a>
                % endif
                % if categ.conferences:
                    <a id="exportIcal${categ.getUniqueId()}" class="i-button icon-calendar arrow exportIcal" data-id="${categ.getUniqueId()}" title="${_("Export to scheduling tool")}"></a>
                    <span><%include file="CategoryICalExport.tpl" args="item=categ"/></span>
                % endif
                <a id="moreLink" class="i-button icon-eye arrow" data-toggle="dropdown" title="${_("View")}"></a>
                <ul class="dropdown">
                    <li><a href="${urlHandlers.UHCategoryOverview.getURL(categ)}">${_("Today's events")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryOverview.getWeekOverviewUrl(categ)}">${_("Week's events")}</a></li>
                    <li><a href="${urlHandlers.UHCalendar.getURL([categ])}">${_("Calendar")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryMap.getURL(categ)}">${_("Category map")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryStatistics.getURL(categ)}">${_("Category statistics")}</a></li>
                </ul>
                <a id="createEventLink" class="i-button icon-plus arrow" data-toggle="dropdown" title="${_("Create new event")}"></a>
                <ul class="dropdown">
                    <li><a href="${urlLecture}">${_("Lecture")}</a></li>
                    <li><a href="${urlMeeting}">${_("Meeting")}</a></li>
                    <li><a href="${urlConference}">${_("Conference")}</a></li>
                </ul>
                % if allowUserModif:
                <a id="manageLink" class="i-button icon-edit arrow" data-toggle="dropdown" title="${_("Management options")}"></a>
                <ul class="dropdown">
                    <li><a href="${urlHandlers.UHCategoryModification.getURL(categ)}">${_("Edit category")}</a></li>
                    <li><a href="${urlHandlers.UHCategoryCreation.getURL(categ)}">${_("Add subcategory")}</a></li>
                </ul>
                % endif
            </div>
            % if isLoggedIn and not isRootCategory:
            <div id="categFavorite" class="group">
                <a class="i-button fav-button icon-only icon-bookmark ${'enabled' if categ in favoriteCategs else ''}" href="#"></a>
            </div>
            % endif
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

    % if isRootCategory or materials or managers or allowUserModif:
    <div class="category-sidebar">
        % if isRootCategory:
            % if isNewsActive:
                <h2 class="icon-bullhorn">
                    ${_("News")}
                    <a href="${ urlHandlers.UHIndicoNews.getURL()}" class="more-icon">${ _("more...") }</a>
                </h2>
                <%include file="WelcomeHeader.tpl" args="tz = timezone"/>
            % endif
            % if upcomingEvents:
                <h2 class="icon-alarm">${_("Upcoming events")}</h2>
                    ${upcomingEvents}
            % endif
        % else:
            % if managers:
                <h2 class="icon-medal">${ _("Managers") }</h2>
                <ul id="manager-list">
                % for type, mgr_name in managers:
                    <li class="${type}">${mgr_name}</li>
                % endfor
                </ul>
            % endif
            % if materials or allowUserModif:
                <div>
                    % if allowUserModif:
                        <div class="right">
                            <a href="#" id="manageMaterial" class="i-button icon-edit"></a>
                        </div>
                    % endif
                    <h2 class="icon-material-download">${ _("Files") }</h2>
                </div>
                <ul>
                % for material in materials:
                    <li>
                        <a class="material-show" data-hidden="true" title="${material.getDescription()}">
                           <div class="left material-title-icon icon-next" ></div>
                           <h3>${material.getTitle()}</h3>
                        </a>
                        <ul class="resource-list" style="display: none">
                        % for resource in material.getResourceList():
                            <li class="icon-file">
                                % if isinstance(resource, Link):
                                <a href="${resource.getURL()}" target="_blank" class="resource"
                                   data-name="${getResourceName(resource)}">
                                    ${getResourceName(resource)}
                                </a>
                                % else:
                                <a href="${urlHandlers.UHFileAccess.getURL(resource)}" target="_blank" class="resource"
                                   data-name="${getResourceName(resource)}"
                                   data-size="${strfFileSize(resource.getSize())}"
                                   data-date="${resource.getCreationDate().strftime("%d %b %Y %H:%M")}">
                                    ${getResourceName(resource)}
                                </a>
                                % endif
                                % if resource.isItselfProtected():
                                    <img src="${Config.getInstance().getSystemIconURL('protected')}" style="vertical-align: middle; border: 0;">
                                % endif
                            </li>
                        % endfor
                        </ul>
                     </li>
                % endfor
                </ul>
            % endif
        % endif
    </div>
    % endif

    <div class="category-content-wrapper">
        <div class="category-content">
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

</div>

<script>
$(document).ready(function(){

    $("#category-toolbar").dropdown();

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

    $('a.resource').qtip({
        content: {
            text: function() {
                var content = $("<div/>");
                var list = $("<ul/>").addClass("category-resource-qtip");
                $("<li/>").append($("<span/>").addClass("bold").append("{0}: ".format($T("Name")))).append($(this).data("name")).appendTo(list);
                if($(this).data("size") !== undefined) {
                    $("<li/>").append($("<span/>").addClass("bold").append("{0}: ".format($T("File size")))).append($(this).data("size")).appendTo(list);
                }
                if($(this).data("date") !== undefined) {
                    $("<li/>").append($("<span/>").addClass("bold").append("{0}: ".format($T("File creation date")))).append($(this).data("date")).appendTo(list);
                }
                list.appendTo(content);
                return content;
            }
        }
    });

    $('.material-show').click(function() {
        var $this = $(this),
            transition_opts = {
                duration: 250,
                easing: 'easeInQuad'
            };

        if ($this.data('hidden')) {
            $this.siblings('.resource-list').slideDown(transition_opts);
            $this.data('hidden', false);
            $this.children(".material-title-icon").removeClass('icon-next').addClass('icon-expand');
        } else {
            $this.siblings('.resource-list').slideUp(transition_opts);
            $this.data('hidden', true);
            $this.children(".material-title-icon").removeClass('icon-expand').addClass('icon-next');
        }
    });
});
</script>

% if isLoggedIn:
    <script type="text/javascript">
        $(document).ready(function(){
            $("#manageMaterial").click(function(){
                    IndicoUI.Dialogs.Material.editor('${categ.getId()}', null, null, null, null,
                            ${jsonEncode(categ.getAccessController().isProtected())}, ${jsonEncode(categ.getMaterialRegistry().getMaterialList(categ))},
                            ${'Indico.Urls.UploadAction.category'}, true);
                 });

            $('.toolbar .i-button').qtip({
                position: {
                    my: 'bottom center',
                    at: 'top center'
                }
            });

            $('.i-button.fav-button').click(function() {
                var $this = $(this);

                if ($this.hasClass('disabled')) {
                    return;
                } else {
                    $this.addClass('disabled');
                    indicoRequest('category.favorites.' + ($this.hasClass("enabled") ? 'delCategory' : 'addCategory'), {
                        categId: '${ categ.getId() }'
                    }, function(result, error) {
                        if(error) {
                            $this.qtip({content: {text: $T('There has been an error. Please reload the page.')}});
                            IndicoUtil.errorReport(error);
                        } else {
                            $this.toggleClass('enabled');
                            $this.removeClass('disabled');
                        }
                    });
                }
            }).qtip({
                hide: {
                        fixed: true,
                        delay: 500
                    },
                content: {
                    text: function() {
                        if ($(this).hasClass('enabled')) {
                            return $T("Remove from your favorites");
                        } else {
                            return format($T('<h3>Add to your favorites</h3><p>This will make events in this category visible on your <a href="{0}">Dashboard</a>.</p>'), [${str(urlHandlers.UHUserDashboard().getURL()) | n,j}]);
                        }
                    }
                }
            })
        });
    </script>
% endif
