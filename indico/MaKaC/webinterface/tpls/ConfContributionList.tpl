<%include file="ConfContributionListFilters.tpl"/>
<div id="contributionList">
    % for contrib in contributions:
        % if contrib.canAccess(accessWrapper):
            <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib"/>
        % elif contrib.canView(accessWrapper):
            <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib"/>
        % endif
    % endfor
</div>