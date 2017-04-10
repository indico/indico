<%page args="form=None"/>

<%
    fields = ['booked_for_user', 'booking_reason']
    field_args = {
        'booking_reason': {'rows': 3, 'placeholder': _(u'Reason...')}
    }
    helpers = {
        'booking_reason': _('Specify why you need this room.'),
        'booked_for_user': _('Specify who will be using the room.')
    }
    ids = {
        'booked_for_user': 'booked-for-user-wrapper',
        'booking_reason': 'booking-reason'
    }
%>

<div id="bookedForInfo">
    <div id="other-user">
        <div class="input-line">
            <input type="radio" name="other_user" id="book-for-me" value="False">
            <label for="book-for-me">${ _("I'll be using the room myself") }</label>
        </div>
        <div class="input-line">
            <input type="radio" name="other_user" id="book-for-someone" value="True">
            <label for="book-for-someone">${ _("I'm booking the room for someone else") }</label>
        </div>
    </div>
    % for field in fields:
        <div id="${ ids[field] }" class="toolbar thin space-before space-after">
            <div class="group">
                ${ form[field](**field_args.get(field, {})) }
                % if helpers.get(field):
                    <i class="info-helper" title="${ helpers[field] }"></i>
                % endif
            </div>
        </div>
    % endfor
    <input id="current-user" type="hidden" value="">
</div>

<script>
    (function() {
        'use strict';

        if (!$('input[name=other_user]:checked').length) {
            $('#current-user').val($('#booked_for_user').val());
            $('#booked_for_user').val('');
        }
        $('#other-user').on('change', function() {
            if ($('input[name=other_user]:checked').val() == 'True') {
                $('#booked-for-user-wrapper').slideDown();
                $('#booked_for_user').val('');
                $('#display-booked_for_user').val('');
            } else {
                $('#booked-for-user-wrapper').slideUp();
                $('#booked_for_user').val($('#current-user').val());
            }
        }).trigger('change');
    })();
</script>
