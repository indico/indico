<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <%include file="ConfContributionListFilters.tpl"/>
    <div id="contributionList">
        % for contrib in contributions:
            <% poster = True if contrib.getSession() and contrib.getSession().getScheduleType() == "poster" else False %>
            % if contrib.canAccess(accessWrapper):
                <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib, poster=poster"/>
            % elif contrib.canView(accessWrapper):
                <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib, poster=poster"/>
            % endif
        % endfor
    </div>
</%block>
