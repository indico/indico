<%page args="contrib=None"/>
    <div class="contributionListContribItem" data-id="${contrib.getId()}" data-session="${contrib.getSession().getId() if contrib.getSession() else '-1'}"
            data-track="${contrib.getTrack().getId() if contrib.getTrack() else '-1'}" data-type="${contrib.getType().getId() if contrib.getType() else '-1'}">
        <div>
            <a href="${str( urlHandlers.UHContributionDisplay.getURL( contrib ))}" style="font-size:14px">${contrib.getTitle()}</a>
        </div>
        <div class="contributionListContribHeader">
            % if contrib.getType() != None:
                <span style="font-weight:bold">${_("Type")}: </span>${contrib.getType().getName()}
            % endif
            % if contrib.getSession() != None:
                <span style="font-weight:bold">${_("Session")}: </span>
                <a class="lightGreyLink" href="${str(urlHandlers.UHSessionDisplay.getURL( contrib.getSession() ))}">${contrib.getSession().getTitle()}</a>
                <div style="background-color: ${contrib.getSession().getColor()};" class="sessionSquare"></div>
            % endif
            % if contrib.getTrack() != None:
                <span style="font-weight:bold">${_("Track")}: </span>${contrib.getTrack().getTitle()}
            % endif
        </div>
        <%block name="description" args="contrib=None">
        </%block>

        <%block name="footer" args="contrib=None">
        </%block>
    </div>