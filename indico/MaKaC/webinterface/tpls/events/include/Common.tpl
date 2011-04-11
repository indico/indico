<%def name="renderDescription(text)">
    % if isStringHTML(text):
        ${text}
    % else:
        <pre>${text}</pre>
    % endif
</%def>

<%def name="renderLocation(location, span='')">
    <%
    correctRoomName = location.room not in ['', '0--', 'Select:']
    prevLocation = location.find('../../location/name')
    %>
    % if not prevLocation or prevLocation != location.find('name'):
        % if location.find('name'):
            ${location.name}
            % if correctRoomName:
            (
            % endif
        % endif
    % endif
    % if correctRoomName:
        % if location.find('roomMapURL'):
            <a href="${location.roomMapURL.text}">
        % endif
        <span class="${span}">${location.room}</span>
        % if location.find('roomMapURL'):
            </a>
        % endif
        % if not prevLocation or prevLocation != location.find('name'):
            % if location.find('name') and correctRoomName:
            )
            % endif
        % endif
    % endif
</%def>

<%def name="renderSpeakers(speaker, span='', title=True)">
    <%
    chairs = []
    for u in speaker.findall('user'):
        user = "%s %s" % (u.name.get('first'), u.name.get('last'))
        if title:
            user = u.title.text + " " + user
        if u.find('organization'):
            user = user + ' (%s)' % u.organization.text
        chairs.append('<span class="%s">%s</span>' % (span, user))
    if speaker.find('UnformatedUser'):
        chairs.append(iconf.chair.UnformatedUser)
    %>
    ${', '.join(chairs)}
</%def>
