<%inherit file="ConfContributionListFilters.tpl"/>

<%block name="staticURL"></%block>
<%block name="listToPDF"></%block>
<%block name="filterHeader">
    <div>
        <input type="text" id="filterContribs" value="" placeholder=${ _("Search in contributions") }>
        <div id="resetFiltersContainer" style="display:none"><a class="fakeLink" style="color: #881122" id="resetFilters">${_("Reset filters")}</a> |</div>
        <a class="fakeLink" id="showFilters">${_("More filters")}</a>
    </div>
</%block>

<%block name="filterSession">
    % if len(session.getSortedSlotList()) > 0:
        <select id="sessionSelector" name="sessionSelector" multiple="multiple">
            <option value="-1" selected="selected">--${_("not specified")}--</option>
            <% from indico.util.date_time import format_date, format_time %>
            % for slot in session.getSortedSlotList():
                <option value="${slot.getId()}" selected="selected">
                    ${format_date(slot.getAdjustedStartDate(tz))}, ${format_time(slot.getAdjustedStartDate(tz))} - ${format_time(slot.getAdjustedEndDate(tz))}
                    % if slot.getTitle():
                        ${slot.getTitle()}
                    % endif
                </option>
            % endfor
        </select>
     % endif
</%block>

<%block name="sessionSelectorName">
    createMultiselect($("#sessionSelector"), "session slots");
</%block>

<%block name="sessionScript">
    % if len(session.getSortedSlotList()) > 0:
        selector = [];
        $("#sessionSelector").multiselect("getChecked").each(function(index) {
            selector.push("[data-session="+ this.value +"]");
        });
        items = items.filter(selector.join(', '));
    % endif
</%block>
