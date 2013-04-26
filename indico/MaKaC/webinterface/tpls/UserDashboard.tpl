<div class="dashboard-tab">
    <div class="quick-access-pane">
        % if redisEnabled:
        <div class="dashboard-col">
            <div id="yourEvents" class="dashboard-box">
                <h3>
                    ${_("Your upcoming events")}
                    % if user.isAdmin():
                        <a href="#" id="refreshRedisLinks" style="float: right;"><span class="icon-refresh contextHelp" title="${_("Admin tool: Refresh Redis links")}"></span></a>
                        <script>
                            $('#refreshRedisLinks').on('click', function(e) {
                                e.preventDefault();
                                var killProgress = IndicoUI.Dialogs.Util.progress();
                                indicoRequest('user.refreshRedisLinks', {
                                    userId: '${ rh._avatar.getId() }'
                                }, function(result, error) {
                                    if(error) {
                                        killProgress();
                                        IndicoUtil.errorReport(error);
                                        return;
                                    }
                                    location.reload();
                                });
                            });
                        </script>
                    % endif
                </h3>
                <ol></ol>
            </div>
        </div>
        % endif
        <div class="dashboard-col">
            <div id="yourCategories" class="dashboard-box">
                <h3>${_("Your categories")}</h3>
                <ol>
                % if not categories:
                    <li class="no-event">
                        <span class="event-title italic text-superfluous">${_("You have no categories.")}</span>
                    </li>
                % else:
                % for category in categories.itervalues():
                    <li><a href="${urlHandlers.UHCategoryDisplay.getURL(category["categ"])}" class="truncate">
                        <span class="category-name truncate-target">${category["categ"].getTitle()}</span>
                        <span class="item-legend">
                            % if category["managed"]:
                            <span title="You have management rights" class="icon-medal contextHelp active"></span>
                            % else:
                            <span title="You have favorited this category" class="icon-star contextHelp active"></span>
                            % endif
                        </span>
                        % if category["path"]:
                            <span class="category-path">${category["path"]}</span>
                        % endif
                    </a></li>
                % endfor
                % endif
                </ol>
            </div>
            <div id="happeningCategories" class="dashboard-box">
                <h3>${_("Happening in your categories")}</h3>
                <ol>
                % if not categories:
                    <li class="no-event">
                        <span class="event-title italic text-superfluous">${_("You have no categories.")}</span>
                    </li>
                % endif
                </ol>
            </div>
        </div>
    </div>
</div>

<script>
$(document).ready(function(){

    /* Time formatting */
    if (currentLanguage === "fr_FR") {
        moment.lang("fr", {
            calendar: {
                lastDay : '[Hier]',
                sameDay : "[Aujourd'hui]",
                nextDay : '[Demain]',
                nextWeek : 'dddd',
                lastWeek : 'DD MMM YYYY',
                sameElse : 'DD MMM YYYY'
            }
        });
    } else if (currentLanguage === "es_ES") {
        moment.lang("es", {
            calendar: {
                lastDay : '[Ayer]',
                sameDay : "[Hoy]",
                nextDay : '[Mañana]',
                nextWeek : 'dddd',
                lastWeek : 'DD MMM YYYY',
                sameElse : 'DD MMM YYYY'
            }
        });
    } else {
        moment.lang("en", {
            calendar: {
                lastDay : '[Yesterday]',
                sameDay : '[Today]',
                nextDay : '[Tomorrow]',
                nextWeek : 'dddd',
                lastWeek : 'DD MMM YYYY',
                sameElse : 'DD MMM YYYY'
            }
        });
    }

    /* AJAX query */
    var managementFilter = ["conference_creator", "conference_chair",
                             "conference_manager", "conference_registrar",
                             "session_manager", "session_coordinator",
                             "contribution_manager"];
    var reviewFilter = ["conference_paperReviewManager", "conference_referee",
                         "conference_editor", "conference_reviewer",
                         "contribution_referee", "contribution_editor",
                         "contribution_reviewer", "track_coordinator"];
    var attendanceFilter = ["conference_participant", "contribution_submission",
                             "abstract_submitter", "registration_registrant",
                             "evaluation_submitter"];

    var api_opts = {
        limit: "10",
        from: "today",
        order: "start",
        userid: "${ rh._avatar.getId() }"
    };

    // Your events
    apiRequest("/user/linked_events", api_opts).done(function (resp) {
        var html = '';
        if (resp.count === 0) {
            html += '<li class="no-event"> \
                         <span class="event-title italic text-superfluous">' + $T("You have no events.") + '</span> \
                     </li>';
        } else {
            $.each(resp.results, function (i, item) {
                html += '<li id="event-' + item.id + '" class="truncate"> \
                             <a href="' + item.url + '" class="truncate"> \
                                 <span class="event-date">' + getDate(item.startDate, item.endDate) + '</span> \
                                 <span class="event-title truncate-target">' + item.title + '</span> \
                                 <span class="item-legend"> \
                                     <span title="' + $T("You have management rights") + '" class="icon-medal contextHelp ' + hasRights(item.roles, managementFilter) + '"></span> \
                                     <span title="' + $T("You are a reviewer") + '" class="icon-reading contextHelp ' + hasRights(item.roles, reviewFilter) + '"></span> \
                                     <span title="' + $T("You are an attendee") + '" class="icon-ticket contextHelp ' + hasRights(item.roles, attendanceFilter) + '"></span> \
                                 </span> \
                             </a>\
                         </li>';
            });
        }
        var list = $("#yourEvents ol");
        list.append(html);
        // Enable tooltips for active roles and delete them for inactive ones
        list.find('.contextHelp[title].active').qtip();
        list.find('.contextHelp[title]:not(.active)').removeAttr('title');
    });

    % if categories:
    // Happening in your categories query
    apiRequest("/user/categ_events", api_opts).done(function(resp) {
        var html = '';
        if (resp.count === 0) {
            html += '<li class="no-event"> \
                         <span class="event-title italic text-superfluous">' + $T("Nothing happening in your categories.") + '</span> \
                     </li>';
        } else {
            $.each(resp.results, function(i, item) {
                html += '<li class="truncate"><a href="' + item.url + '" class="truncate"> \
                            <span class="event-date">' + getDate(item.startDate, item.endDate) + '</span> \
                            <span class="event-title truncate-target">' + item.title + '</span> \
                            <span class="event-category">' + item.category + '</span> \
                         </a></li>';
            });
        }
        $("#happeningCategories ol").append(html);
    });
    % endif

    var getDate = function(startDate, endDate) {
        if (moment(startDate.date) < moment() && moment() < moment(endDate.date)) {
            return $T("Now");
        } else {
            return moment(startDate.date).calendar();
        }
    };

    var hasRights = function(rights, filter) {
        for (var i=0; i < rights.length; i++) {
            for (var j=0; j < filter.length; j++) {
                if (rights[i] === filter[j]) {
                    return "active";
                }
            }
        }
        return "";
    };
});
</script>