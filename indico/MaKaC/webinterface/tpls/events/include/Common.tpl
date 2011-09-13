<%def name="renderDescription(text)">
    % if isStringHTML(text):
        ${text}
    % else:
        <pre>${text}</pre>
    % endif
</%def>

<%def name="renderLocation(item, parent=None, span='')">
    <% location, room, url = getLocationInfo(item) %>
    % if location and not parent or getLocationInfo(parent)[0] != location:
         ${location}
         % if room:
             (
         % endif
    % endif
    % if room:
        ${'<a href="%s">'%url if url else ''}
            <span class="${span}">${room}</span>
        ${'</a>' if url else ''}
        % if location and not parent or getLocationInfo(parent)[0] != location:
            )
        % endif
    % endif
</%def>

<%def name="renderLocationAdministrative(item, parent=None)">
<% location, room, url = getLocationInfo(item) %>
    % if location and not parent or getLocationInfo(parent)[0] != location:
         <b>${location}</b>
         % if room:
             ( ${room} )
         % endif
    % elif room:
         ${room}
    % endif
</%def>

<%def name="renderLocationText(item, parent=None)">
    <% location, room, url = getLocationInfo(item) %>
    % if location and not parent or getLocationInfo(parent)[0] != location:
         <b>${location}</b>
         % if room:
             (
         % endif
    % endif
    % if room:
        ${room}
        % if location and not parent or getLocationInfo(parent)[0] != location:
            )
        % endif
    % endif
</%def>

<%def name="renderUsers(userList, unformatted='', spanClass='', title=True, italicAffilation=False, useSpan=True, separator=', ')">
    <%
    result = []
    for user in userList:
        userText = "%s %s" % (user.getFirstName(), user.getFamilyName())
        if title:
            userText = user.getTitle() + " " + userText
        if user.getAffiliation():
            affiliation = user.getAffiliation()
            if italicAffilation:
                affiliation = '<i>' +  affiliation + '</i>'
            userText += ' (%s)' % affiliation
        if useSpan:
            result.append('<span class="%s">%s</span>' % (spanClass, userText))
        else:
            result.append(userText)
    if unformatted:
        result.append(unformatted)
    %>
    ${separator.join(result)}
</%def>

<%def name="renderEventTime(startDate, endDate, timezone, strong=True)">
    <% timeFormat = "<strong>%s</strong>" if strong else "%s" %>
    % if getDate(startDate) == getDate(endDate):
        ${prettyDate(startDate)}
        % if not isTime0H0M(startDate):
            from ${timeFormat % getTime(startDate)}
        % endif
        % if not isTime0H0M(endDate):
            to ${timeFormat % getTime(endDate)}
        % endif
    % else:
        from ${prettyDate(startDate)} at ${timeFormat % getTime(startDate)}
        to ${prettyDate(endDate)} at ${timeFormat % getTime(endDate)}
    % endif
    (${str(timezone)})
</%def>

<%def name="renderEventTime2(startDate, endDate, timezone='')">
    % if getDate(startDate) == getDate(endDate):
        ${prettyDate(startDate)}
        % if not isTime0H0M(startDate):
            - <u>${ getTime(startDate)}</u>
        % endif
    % else:
        from ${prettyDate(startDate)} (${getTime(startDate)})
        to ${prettyDate(endDate)} (${getTime(endDate)})
    % endif
    % if timezone!='':
        (${str(timezone)})
    % endif

</%def>

<%def name="renderEventTimeText(startDate, endDate)">
    % if getDate(startDate) == getDate(endDate):
        ${prettyDate(startDate)}
    % else:
        ${prettyDate(startDate)} to ${prettyDate(endDate)}
    % endif

</%def>

<%def name="renderEventTimeCompact(startDate, endDate)">
    % if getDate(startDate) == getDate(endDate):
        ${prettyDate(startDate)}
        % if not isTime0H0M(startDate):
            - <u>${ getTime(startDate)}</u>
        % endif
    % else:
        from <b>${prettyDate(startDate)} (${getTime(startDate)})</b>
        to <b>${prettyDate(endDate)} (${getTime(endDate)})</b>
    % endif
</%def>

