<%page args="contributions=None, accessWrapper=None, poster=False"/>
<%include file="SessionContributionListFilters.tpl"/>

<div id="contributionList">
    % for contrib in contributions:
        % if contrib.canAccess(accessWrapper):
            <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib, slot=True, poster=poster"/>
        % elif contrib.canView(accessWrapper):
            <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib, slot=True, poster=poster"/>
        % endif
    % endfor
</div>