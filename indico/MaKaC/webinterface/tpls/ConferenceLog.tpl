<%
    from indico.util.date_time import format_human_date, format_time
    from indico.util.struct import iterators
    from MaKaC.common.timezoneUtils import nowutc
%>

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
        <div class="group i-selection left">
            <span class="i-button label">${_("Filter by")}</span>
            <input type="checkbox" id="emailLog" checked>
            <label for="emailLog" class="i-button">${_("Email")}</label>
            <input type="checkbox" id="actionLog" checked>
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
        <div id="searchBox" class="group right">
            <span class="i-button label">
                <span class="icon-search" aria-hidden="true"></span>
            </span>
            <input type="text" id="searchInput"/>
        </div>
    </div>
</div>

<div id="logs">
    <h3 id="emptyLog" class="i-table emphasis border hidden">
        ${_("The log is empty")}
    </h3>

    <h3 id="nothingToShow" class="i-table emphasis border hidden">
        ${_("All results hidden")}
    </h3>

    % for day_entry in iterators.SortedDictIterator(log_dict, reverse=True):
    <% key = day_entry[0] %>
    <% value = day_entry[1] %>

    <h3 class="i-table searchable">${format_human_date(key).title()}</h3>
    <table id="log-table-${key}" class="i-table log-table">
        % for line in value:
        <tr class="i-table interactive ${line.getLogType()}" >
                <td class="i-table ${get_icon(line.getLogType())}" aria-hidden="true"></td>
                <td class="i-table log-module searchable">${line.getModule()}</td>
                <td class="i-table log-subject searchable">${line.getLogSubject()}</td>
                <td class="i-table log-stamp text-superfluous">
                % if line.getResponsibleName() != "System":
                    ${_("by {user} at {time}").format(user='<span class="text-normal searchable user-name">{0}</span>'.format(line.getResponsibleName()),
                                                      time='<span class="text-normal">{0}</span>'.format(format_time(line.getLogDate(), "medium")))}
                % else:
                    <span class="text-normal">${format_time(line.getLogDate(), "medium")}</span>
                % endif
                </td>
        </tr>
        <tr class="i-table content-wrapper weak-hidden">
            <td class="i-table" colspan="4">
                <table class="i-table no-margin">
                        % if len(line.getLogInfo()) == 1 and "subject" in line.getLogInfo():
                        <tr class="i-table content">
                            <td class="i-table caption log-caption"></td>
                            <td class="i-table value empty">${_("No further information to show.")}</td>
                        </tr>
                        % else:
                            % for info in line.getLogInfoList():
                            <% caption = info[0]%>
                            <% value = info[1]%>
                            <tr class="i-table content">
                                <td class="i-table caption log-caption">${caption}</td>
                                <td class="i-table value searchable">${value}</td>
                            </tr>
                            % endfor
                        % endif
                </table>
            </td>
        </tr>

        % endfor
    </table>
    % endfor
</div>


<script>
$(document).ready(function(){

    /* Initializations */
    if ($(".log-table").length === 0) {
        $("#emptyLog").removeClass("hidden");
    }

    /* UI animations */
    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });

    $("tr.i-table.interactive").click(function() {
        toggleExpandedRow($(this));
    });

    var toggleExpandedRow = function(interactive_row) {
        if (interactive_row.hasClass("active")) {
            collapseRow(interactive_row);
        } else {
            expandRow(interactive_row);
        }
    }

    var expandRow = function(interactive_row) {
        interactive_row.addClass("active border-bottom-none");
        interactive_row.next().removeClass("weak-hidden")
                              .children("td")
                              .wrapInner('<div style="display: none;" />')
                              .parent()
                              .find("td > div")
                              .slideDown(400, function() {
                                  var $set = $(this);
                                  $set.replaceWith($set.contents());
                              });
    };

    var collapseRow = function(interactive_row) {
        interactive_row.removeClass("active");

        interactive_row.next().children("td")
                              .wrapInner('<div style="display: block;" />')
                              .parent()
                              .find("td > div")
                              .slideUp(400, function() {
                                  var $set = $(this);
                                  $set.replaceWith($set.contents());
                                  interactive_row.removeClass("border-bottom-none");
                                  interactive_row.next().addClass("weak-hidden");
                              });
    };

    /* Event checkbox selector behavior */
    $(".i-selection input[type=checkbox]").change(function() {
        applyFilters();
    });

    // Because IE8 does not trigger change event for input elements
    $('.i-selection input[type=checkbox] + label').click(function () {
        var $checkbox = $(this).prev();
        $checkbox.prop("checked", !$checkbox.prop("checked"));
        $checkbox.trigger("change");
        return false;
     });

    /* Action buttons behavior */
    $("#expandAll").click(function(e) {
        e.preventDefault();
        $("tr.i-table.interactive:visible").addClass("active border-bottom-none").next().removeClass("weak-hidden");
    });

    $("#collapseAll").click(function(e) {
        e.preventDefault();
        $("tr.i-table.interactive").removeClass("active border-bottom-none").next().addClass("weak-hidden");
    });

    $("#searchInput").realtimefilter({
        callback: function() {
            applyFilters();
        }
    });

    var resultCache = [];
    var allTableTitles = $("h3.i-table");
    var allTables = $(".log-table");
    var allRows = $("tr.i-table.interactive");
    var allContentRows = $("tr.i-table.content-wrapper");

    var applyFilters = function(){
        var checkboxes = $(".i-selection input:checkbox:checked");
        var items = getSearchFilteredItems().filter(getCheckboxFilteredItems(checkboxes));

        allTableTitles.show();
        allTables.show();
        allRows.hide();
        allContentRows.addClass("weak-hidden");

        showRows(items);
        hideEmptyTables();

        // Needed because $(window).scroll() is not called when hiding elements
        // causing scrolling elements to be out of place.
        $(window).trigger("scroll");
    };

    var getSearchFilteredItems = function() {
        var term = $("#searchInput").val();
        if (resultCache[term] !== undefined) {
            return resultCache[term];
        }
        var items = $("h3.i-table.searchable").textContains(term).next().find("tr.i-table.interactive");
        items = items.add($("tr.i-table.interactive .searchable").textContains(term).parents("tr.i-table.interactive"));
        resultCache[term] = items;
        return items;
    };

    var getCheckboxFilteredItems = function(checkboxes) {
        return function(i) {
            var $this = $(this);
            var flag = false;

            checkboxes.each(function(){
                if ($this.is("tr.i-table." + this.id)) {
                    flag = true;
                }
            });

            return flag;
        }
    };

    var showRows = function(items) {
        items.show();
        items.each(function() {
            if ($(this).hasClass("active")) {
                $(this).next(".content-wrapper").removeClass("weak-hidden");
            } else {
                $(this).next(".content-wrapper").addClass("weak-hidden");
            }
        });
    };

    var hideEmptyTables = function() {
        $emptyTables = $("tr.i-table.interactive:hidden").parents("table.i-table").not($("tr.i-table.interactive:visible").parents("table.i-table"));
        $emptyTables.hide();
        $emptyTables.prev().hide();

        if ($(".log-table").length > 0 &&
            $(".log-table:visible").length === 0) {
            $("#nothingToShow").removeClass("hidden");
        } else {
            $("#nothingToShow").addClass("hidden");
        }
    };
});
</script>
