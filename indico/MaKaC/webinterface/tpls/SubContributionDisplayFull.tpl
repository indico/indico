<%inherit file="SubContributionDisplayMin.tpl"/>

<%block name="speakers">
    <div class="subContributionSpeakerList">
        <% speakers = [] %>
        % for speaker in SubContrib.getSpeakerList():
            <% speakers.append(speaker.getDirectFullName()) %>
        % endfor
        % if speakers:
            ${("Presented by")} <span style="font-weight: bold">${", ".join(speakers)} </span>
        % endif
    </div>
</%block>