<%page args="minutes='off'"/>
<%namespace name="common" file="Common.tpl"/>

<table class="eventDetails">
    <tbody>
    % if iconf.find('description'):
    <tr>
        <td class="leftCol">Description</td>
        <td>${common.renderDescription(iconf.description.text)}</td>
    </tr>
    % endif

    % if iconf.find('participants'):
    <tr>
        <td class="leftCol">Participants</td>
        <td>${iconf.participants}</td>
    </tr>
    % endif

    % if webcast and webcast.displayURL:
    <tr id="webCastRow"">
        <td class="leftCol">
        % if webcast.title == 'live webcast':
            Live Webcast
        % elif webcast.title == 'forthcoming webcast':
            Webcast
        % endif
        </td>
        <td>
        % if webcast.title == 'live webcast':
             <a href="${webcast.displayURL}"><strong>View the live webcast</strong></a>
             % if webcast.find('locked') == 'yes':
                <img src="images/protected.png" border="0" alt="locked" style="margin-left: 3px;"/>
             % endif
        % elif webcast.title == 'forthcoming webcast':
             Please note that this event will be available <em>live</em> via the
             <a href="${webcast.displayURL}"><strong>Webcast Service</strong>.</a>
        % endif
        </td>
    </tr>
    % endif

    % if len(materials) > 0:
    <tr id="materialList">
        <td class="leftCol">Material</td>
        <td>
            <div class="materialList clearfix">
            % for material in materials:
                <%include file="Material.tpl" args="material=material"/>
            % endfor
            </div>
            % if minutes == 'on':
                % for minutes in iconf.findall('material/minutesText'):
                    <center>
                        <div class="minutesTable">
                            <h2>Minutes</h2>
                            <span>${common.renderDescription(minutes.text)}</span>
                        </div>
                    </center>
                % endfor
            % endif
        </td>
    </tr>
    % endif

    % if len(lectures) > 0:
    <tr id="lectureLinks">
        <td class="leftCol">Other occasions</td>
        <td>
        % for lecture in lectures:
            <a href="materialDisplay.py?materialId=${lecture.ID}&confId=${iconf.ID}">\
<img src="images/${lecture.title}.png" alt="${lecture.title}"/></a>&nbsp;
        % endfor
        </td>
    </tr>
    % endif

    % if iconf.find('apply'):
    <tr>
        <td class="leftCol">Registration</td>
        <td>
            Want to participate?
            <span class="fakeLink" id="applyLink">Apply here</span>
            <script type="text/javascript">
                $E('applyLink').observeClick(function(){new ApplyForParticipationPopup("${iconf.ID}")});
            </script>
        </td>
    </tr>
    % endif

    % if iconf.find('evaluationLink'):
    <tr>
        <td class="leftCol">Evaluation</td>
        <td><a href="${iconf.evaluationLink}">Evaluate this event</a></td>
    </tr>
    % endif

    % if iconf.find('organiser'):
    <tr>
        <td class="leftCol">Organised by</td>
        <td>${iconf.organiser}</td>
    </tr>
    % endif

    <%include file="Chatrooms.tpl"/>

    <%include file="VideoServices.tpl"/>

    % if iconf.find('supportEmail'):
    <tr>
        <td class="leftCol">${iconf.supportEmail.get('caption')}</td>
        <td><a href="mailto:${iconf.supportEmail}">${iconf.supportEmail}</a></td>
    </tr>
    % endif

    </tbody>
</table>