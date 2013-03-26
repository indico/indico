<%
    import datetime

    from indico.util.struct import iterators
    from indico.util.string import truncate
    from indico.util.date_time import format_date, format_time
    from MaKaC.common.timezoneUtils import nowutc

    today = nowutc()
    yesterday = nowutc() - datetime.timedelta(days=1)
%>

<%def name="parse_day(log_day_date)">
    % if log_day_date == today.date():
        ${_("Today")}
    % elif log_day_date == yesterday.date():
        ${_("Yesterday")}
    % else:
        ${format_date(log_day_date, "long")}
    % endif
</%def>

<%def name="get_icon(log_type)">
    % if log_type == "emailLog":
        icon-mail
    % elif log_type == "actionLog":
        icon-key-A
    % endif
</%def>

<div class="groupTitle">
    <span class="icon-clipboard" aria-hidden="true"></span>
    <span>${_("Event Log")}</span>
</div>

<div id="headPanel" class="follow-scroll">
    <div id="button-menu" class="toolbar">
        <div id="eventFilter" class="group labelled selection left">
            <span class="i-button label">${_("Filter by")}</span>
            <input type="checkbox" id="emailLog" name="view_filter" checked>
            <label for="emailLog" class="i-button">${_("Email")}</label>
            <input type="checkbox" id="actionLog" name="view_filter" checked>
            <label for="actionLog" class="i-button">${_("Action")}</label>
        </div>
        <div id="expandControlls" class="group left">
            <a id="expandAll" class="i-button" title="${"Expand all"}" href="#">
                <span class="icon-stack-plus" aria-hidden="true"></span>
            </a>
            <a id="collapseAll" class="i-button" title="${"Collapse all"}" href="#">
                <span class="icon-stack-minus" aria-hidden="true"></span>
            </a>
        </div>
        <div id="searchBox" class="group labelled right">
            <span class="i-button label">
                <span class="icon-search" aria-hidden="true"></span>
            </span>
            <div class="text-input">
                <input type="text" id="searchInput"/>
                <span class="reset-input icon-close" aria-hidden="true"></span>
            </div>
        </div>
    </div>
</div>

<div id="emptyLog" class="hidden">
    <div class="table-title emphasis">
         ${_("The log is empty")}
    </div>
</div>

<div id="nothingToShow" class="hidden">
    <div class="table-title emphasis">
        ${_("All results hidden")}
    </div>
</div>

% for day_entry in iterators.SortedDictIterator(log_dict, reverse=True):
<% key = day_entry[0] %>
<% value = day_entry[1] %>
<div id="log-table-${key}">
    <div class="table-title info">
        ${parse_day(key)}
    </div>
    % for line in value:
    <div class="table-row interactive ${line.getLogType()}" aria-hidden="true">

        <div class="inline">
            <span class="table-cell ${get_icon(line.getLogType())}"></span>
            <span class="table-cell fixed info">${line.getModule()}</span>
            <span class="table-cell info">${line.getLogSubject()}</span>
            <span class="table-cell right">
                ${format_time(line.getLogDate(), "medium")}
            </span>
            % if line.getResponsibleName() != "System":
            <span class="table-cell right info">
                ${_("By ")} ${line.getResponsibleName()} ${_(" at")}
            </span>
            % endif
        </div>

        <div class="info-wrapper weak-hidden">
        % if len(line.getLogInfo()) == 1 and "subject" in line.getLogInfo():
            <div class="content-row clearfix">
                <span class="table-cell fixed v-growing"></span>
                <span class="table-cell empty v-growing">${_("No further information to show.")}</span>
            </div>
        % else:
            % for info in line.getLogInfoList():
                <% caption = info[0]%>
                <% value = info[1]%>
                <div class="content-row clearfix">
                    <span class="table-cell fixed v-growing">${caption}</span>
                    <span class="table-cell v-growing info">${value}</span>
                </div>
            % endfor
        % endif
        </div>
    </div>
    % endfor
</div>
% endfor

<script>
$(document).ready(function(log_view){

    if ($("[id*=log-table-]").length === 0) {
        $("#emptyLog").removeClass("hidden");
    }

    /* UI animations */
    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });

    $(".table-row .inline").click(function() {
        slideRow($(this));
    });

    var slideRow = function(row_inline) {
        row_inline.parent().toggleClass("active");
        row_inline.toggleClass("active");
        row_inline.siblings(".info-wrapper").slideToggle();
    }

    var slideRowDown = function(row_inline) {
        row_inline.parent().addClass("active");
        row_inline.addClass("active");
        row_inline.siblings(".info-wrapper").slideDown();
    }

    var slideRowUp = function(row_inline) {
        row_inline.parent().removeClass("active");
        row_inline.removeClass("active");
        row_inline.siblings(".info-wrapper").slideUp();
    }

    /* Event checkbox selector behavior */
    $(".group.selection input[type=checkbox]").change(function() {
        applyFilters();
    });

    /* Action buttons behavior */
    $("#expandAll").click(function(e) {
        e.preventDefault();
        $(".table-row .inline").each(function() {
            slideRowDown($(this));
        })
    });

    $("#collapseAll").click(function(e) {
        e.preventDefault();
        $(".table-row .inline").each(function() {
            slideRowUp($(this));
        })
    });

    /* Search behavior */
    $("#searchBox input").focus(function() {
        $("#searchBox .text-input").addClass("active");
    });

    $("#searchBox input").focusout(function() {
        $("#searchBox .text-input").removeClass("active");
    });

    $("#searchInput").keyup(function() {
        applyFilters();
        updateResetButton();
    });

    $("#searchBox .reset-input").click(function(e) {
        e.preventDefault();
        $("#searchInput").attr("value", "");
        applyFilters();
        updateResetButton();
    })

    var resultCache = [];
    var allTables = $("[id*=log-table-]");
    var allRows = $(".table-row");

    var applyFilters = function(){
        allTables.show();
        allRows.hide();

        getSearchFilteredItems().show();
        getCheckboxFilteredItems().hide();
        hideEmptyTables();
    };

    var getCheckboxFilteredItems = function() {
        var checkboxes = $(".group.selection input[type=checkbox]:not(:checked)");

        var items = $();
        checkboxes.each(function(){
            items = items.add($("div.table-row." + $(this).attr("id") + ":visible"));
        });

        return items;
    }

    var getSearchFilteredItems = function() {
        var term = $("#searchInput").attr("value");
        if (resultCache[term] == undefined) {
            var items = $(".table-title.info:contains('"+ term +"')").siblings(".table-row");
            items = items.add($(".table-row .info:contains('"+ term +"')").parents(".table-row"));
            resultCache[term] = items;
        } else {
            var items = resultCache[term];
        }

        return items;
    }

    var hideEmptyTables = function() {
        $(".table-row:hidden").parent().not($(".table-row:visible").parent()).hide();

        if ($("[id*=log-table-]").length > 0 &&
            $("[id*=log-table-]:visible").length === 0) {
            $("#nothingToShow").removeClass("hidden");
        } else {
            $("#nothingToShow").addClass("hidden");
        }
    }

    var updateResetButton = function() {
        if ($("#searchInput").attr("value") === "") {
            $(".reset-input").css('visibility', 'hidden');
        } else {
            $(".reset-input").css('visibility', 'visible');
        }
    }

})
</script>
