<%page args="form=None"/>

<%
    work_start = room.location.working_time_start
    work_end = room.location.working_time_end
%>

% if form.needs_assistance:
    <div>
        ${ form.needs_assistance() }
        ${ form.needs_assistance.label(style='font-weight: normal;') }
        <i class="info-helper"
           title="${ _('A technician will arrive about 10 minutes before the event to help you start up the room equipment (microphone, projector, etc.)') }"></i>
    </div>
% endif
