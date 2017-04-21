<%page args="form=None"/>

<%
    eq_list = list(form.used_equipment)
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

% if eq_list:
    <div>
        ${ form.uses_vc() }
        ${ form.uses_vc.label(style='font-weight: normal;') }
        <i class="info-helper" title="${ _('Check ONLY if you are actually going to use it') }"></i>
    </div>
    <ul id="videoconferenceOptions" class="weak-hidden">
        % for subfield in [form.needs_vc_assistance] + eq_list:
            % if subfield.short_name == 'needs_vc_assistance' and (start_dt.time() < work_start or start_dt.time() > work_end):
                <li class="js-vc-row semantic-text disabled" title="${ _('Assistance is not available because start time of booking is not within working hours.') }">
                    ${ subfield(disabled=True) }
                    ${ subfield.label(style='font-weight: normal;') }
                </li>
            % else:
                <li class="js-vc-row">
                    ${ subfield() }
                    ${ subfield.label(style='font-weight: normal;') }
                </li>
            % endif

        % endfor
    </ul>
% endif

<script>
    $('.js-vc-row input:checkbox[disabled]').attr('data-initially-disabled', '');
    $('#uses_vc').on('change', function() {
        if (this.checked) {
            $('#videoconferenceOptions').slideDown();
        } else {
            $('#videoconferenceOptions').slideUp();
        }

        $('.js-vc-row input:checkbox:not([data-initially-disabled])').prop('disabled', !this.checked);
        if (!this.checked) {
            $('.js-vc-row input:checkbox').prop('checked', false);
        }
    }).trigger('change');
</script>
