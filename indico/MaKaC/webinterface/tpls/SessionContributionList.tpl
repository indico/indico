<%page args="contributions=None, accessWrapper=None"/>
<%include file="SessionContributionListFilters.tpl"/>

<div id="contributionList">
    % for contrib in contributions:
        % if contrib.canAccess(accessWrapper):
            <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib, slot=True"/>
        % elif contrib.canView(accessWrapper):
            <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib, slot=True"/>
        % endif
    % endfor
</div>