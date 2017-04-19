<% from indico.web.forms.jinja_helpers import render_field %>
<%page args="form=None"/>

<%
    fields = ['room_usage', 'booked_for_user', 'booking_reason']
    field_args = {
        'booking_reason': {'rows': 3, 'placeholder': _(u'Reason...')}
    }
    helpers = {
        'booking_reason': _('Specify why you need this room.'),
        'booked_for_user': _('Specify who will be using the room.')
    }
    ids = {
        'booked_for_user': 'booked-for-user-wrapper',
        'booking_reason': 'booking-reason',
        'room_usage': 'room-usage'
    }
%>

<div id="bookedForInfo">
    % for field in fields:
        <div id="${ ids[field] }" class="toolbar thin space-before space-after">
            <div class="group">
                ${ render_field(form[field], field_args.get(field, {})) }
                % if helpers.get(field):
                    <i class="info-helper" title="${ helpers[field] }"></i>
                % endif
            </div>
        </div>
    % endfor
</div>

<script>

    function checkRoomUsageState(selectedOption) {
        if (selectedOption == 'other_user') {
            $('#booked-for-user-wrapper').slideDown().find('input[type=hidden]').prop('disabled', '');
        } else {
            $('#booked-for-user-wrapper').slideUp().find('input[type=hidden]').prop('disabled', 'disabled');
        }
    }

    (function() {
        'use strict';

        checkRoomUsageState($('[name=room_usage]:checked').val());
        $('input[name=room_usage]').on('change', function() {
            checkRoomUsageState($(this).val());
        });
    })();
</script>
