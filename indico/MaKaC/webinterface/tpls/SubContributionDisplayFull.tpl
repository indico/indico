<%inherit file="SubContributionDisplayMin.tpl"/>

<%block name="speakers">
    <div class="subContributionSpeakerList">
        <% speakers = [] %>
        % for speaker in SubContrib.getSpeakerList():
            <% speakers.append(speaker.getDirectFullName()) %>
        % endfor
        % if speakers:
            ${_("Presented by")} <span style="font-weight: bold">${", ".join(speakers)} </span>
        % endif
    </div>
</%block>
<%block name="reportNumber">
    % if SubContrib.getReportNumberHolder().listReportNumbers():
        <div><span style="font-weight:bold">${_("Report Numbers")}:</span>
        % for reportNumber in SubContrib.getReportNumberHolder().listReportNumbers():
            % if reportNumberSystems[reportNumber[0]]["url"]:
                <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
            % else:
                ${reportNumber[1]}
            % endif
        % endfor
        </div>
    % endif
</%block>