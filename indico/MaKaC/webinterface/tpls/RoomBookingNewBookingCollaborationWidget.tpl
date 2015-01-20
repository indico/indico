<%page args="form=None"/>
<% eq_list = list(form.used_equipment) %>

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
            <li class="js-vc-row">
                ${ subfield() }
                ${ subfield.label(style='font-weight: normal;') }
            </li>
        % endfor
    </ul>
% endif

<script>
    $('#uses_vc').on('change', function() {
        if (this.checked) {
            $('#videoconferenceOptions').slideDown();
        } else {
            $('#videoconferenceOptions').slideUp();
        }

        $('.js-vc-row input:checkbox').prop('disabled', !this.checked);
        if (!this.checked) {
            $('.js-vc-row input:checkbox').prop('checked', false);
        }
    }).trigger('change');
</script>
