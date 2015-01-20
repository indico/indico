<%namespace name="common" file="include/Common.tpl"/>

<%def name="printSessionInfo(item)">
    ${item.getSession().getTitle()}<br/>
    % if item.getDescription():
        ----------------------------------------<br/>
        ${item.getDescription()}<br/>
    % endif
    ----------------------------------------<br/>
    % for subitem in item.getSchedule().getEntries():
        <br/>
        <%
            if subitem.__class__.__name__ != 'BreakTimeSchEntry':
                subitem = subitem.getOwner()
        %>
        <% subType = getItemType(subitem) %>
        % if getItemType(subitem) == "Break":
            ${printBreakInfo(subitem)}
        % elif getItemType(subitem) == "Contribution":
            ${printContributionInfo(subitem)}
        % endif
    % endfor
    ----------------------------------------<br/>
</%def>

<%def name="printContributionInfo(item)">
   % if not isTime0H0M(item.getAdjustedStartDate(timezone)):
        ${getTime(item.getAdjustedStartDate(timezone))}&nbsp;
   % endif
    ${item.getTitle()}&nbsp;
   % if item.getSpeakerList() or item.getSpeakerText():
        (${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), title=False, useSpan=False)})
   % endif
   <br/>
   % if item.getDescription():
        ${item.getDescription()}
   % endif
   <br/>
   % if item.getSubContributionList():
       % for subcont in item.getSubContributionList():
           <br/>
           ${printSubContributionInfo(subcont)}
       % endfor
% endif
</%def>

<%def name="printSubContributionInfo(item)">
    &nbsp;&nbsp;&nbsp;o ${item.getTitle()}&nbsp;
   % if item.getSpeakerList() or item.getSpeakerText():
        (${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), useSpan=False)})
   % endif
   <br/>
   % if item.getDescription():
        ${item.getDescription()}
   % endif
   <br/>
</%def>


<%def name="printBreakInfo(item)">
   % if not isTime0H0M(item.getAdjustedStartDate(timezone)):
        ${getTime(item.getAdjustedStartDate(timezone))}&nbsp;
   % endif
    ${item.getTitle()}
    <br/>
</%def>


<% location, room, url = getLocationInfo(conf) %>

${ conf.getTitle()}
${ prettyDate(conf.getAdjustedStartDate()) }
% if conf.getAdjustedStartDate().date() != conf.getAdjustedEndDate().date():
   ${_("to")} ${prettyDate(conf.getAdjustedEndDate())}
  <br/><br/>
% endif
% if conf.getDescription():
    Description: ${conf.getDescription()}<br/>
% endif

% if conf.getParticipation().displayParticipantList() and conf.getParticipation().getParticipantList():
    Participants: ${ conf.getParticipation().getPresentParticipantListText() }<br/>
% endif

% for index, item in enumerate(entries):

    <%
    type = getItemType(item)
    date = getDate(item.getAdjustedStartDate(timezone))
    previousItem = entries[index - 1] if index - 1 >= 0 else None
    nextItem = entries[index + 1] if index + 1 < len(entries) else None
    %>

    % if (not previousItem or date != getDate(previousItem.getAdjustedStartDate(timezone))):
        <br/>
        ${prettyDate(item.getAdjustedStartDate(timezone))}<br/>
        __________________________________________________________<br/>
    % endif
    <br/>
    % if type == "Break":
       ${printBreakInfo(item)}
    % elif type == "Contribution":
       ${printContributionInfo(item)}
    % elif type == "Session":
       ${printSessionInfo(item)}
    % endif
% endfor