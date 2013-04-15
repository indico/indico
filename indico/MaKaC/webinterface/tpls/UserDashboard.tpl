<%
    from indico.util.date_time import format_human_date
%>

<div class="dashboard-tab">
    <div class="quick-access-pane">
        <div class="dashboard-col">
            <div id="events" class="dashboard-box">
                <h3>${_("Your events")}</h3>
                <ol>
                % if len(events) == 0:
                    <li class="no-event"><a>
                        <span class="event-title italic text-superfluous">${_("You have no events.")}</span>
                    </a></li>
                % else:
                % for event in events.values():
                    <li><a href="${event["url"]}" class="truncate">
                        <span class="event-date">${format_human_date(event["date"]).title()}</span>
                        <span class="event-title truncate-target">${event["title"]}</span>
                        <span class="item-legend">
                            <span title="You have management rights" class="icon-medal contextHelp"></span>
                            <span title="You are a reviewer" class="icon-reading contextHelp"></span>
                            <span title="You are an atendee" class="icon-ticket contextHelp"></span>
                        </span>
                    </a></li>
                % endfor
                % endif
                </ol>
            </div>
        </div>
        <div class="dashboard-col">
            <div id="yourCategories" class="dashboard-box">
                <h3>${_("Your categories")}</h3>
                <ol>
                % if len(categories) == 0:
                    <li class="no-event"><a>
                        <span class="event-title italic text-superfluous">${_("You have no categories.")}</span>
                    </a></li>
                % else:
                % for category in categories.values():
                    <li><a href="${urlHandlers.UHCategoryDisplay.getURL(category["categ"])}" class="truncate">
                        <span class="category-title truncate-target">${category["categ"].getTitle()}</span>
                        <span class="item-legend">
                            % if category["managed"] is True:
                            <span title="You have management rights" class="icon-medal contextHelp active"></span>
                            % else:
                            <span title="You have favorited this category" class="icon-star contextHelp active"></span>
                            % endif:
                        </span>
                        <span class="category-path">${category["path"]}</span>
                    </a></li>
                % endfor
                % endif
                </ol>
            </div>
            <div id="happeningCategories" class="dashboard-box">
                <h3>${_("Happening in your categories")}</h3>
                <ol>
                <%doc>
                % if len(events) != 0:
                    <li class="no-event"><a>
                        <span class="event-title italic text-superfluous">${_("You have no categories.")}</span>
                    </a></li>
                % else:
                % endif
                </%doc>
                </ol>
            </div>
        </div>
    </div>
</div>

<script>
$(document).ready(function(log_view){
    $.getJSON("http://pcuds43.cern.ch:8000/indico/export/categ/favorites.json?ak=368612c2-7029-4d28-a54b-8eb036b8f114&limit=10&from=today&order=start", function(data) {
        $.each(data.results, function(i, item) {
            $("#happeningCategories ol").append(
                    '<li class="truncate"><a href="' + item.url + '" class="truncate"> \
                        <span class="event-date">' + item.startDate.date + '</span> \
                        <span class="event-title truncate-target">' + item.title + '</span> \
                        <span class="event-category">' + item.category + '</span> \
                     </a></li>');
        });
    });

    $(".contextHelp[title]").qtip("disable");
    $(".contextHelp[title].active").qtip("enable");
});
</script>