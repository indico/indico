<%page args="form=None"/>

<%
    fields = ['booked_for_user', 'contact_email', 'contact_phone', 'booking_reason']
    field_args = {
        'booking_reason': {'rows': 3, 'placeholder': _(u'Reason...')}
    }
    helpers = {
        'contact_email': 'You can specify multiple email addresses separated by commas.',
        'booking_reason': 'Specify why you need this room.'
    }
%>

<div id="bookedForInfo">
    % for field in fields:
        <div class="toolbar thin space-before space-after">
            <div class="group">
                % if not form[field].short_name == 'booking_reason':
                    <span class="i-button label heavy">
                        ${ form[field].label.text }
                    </span>
                % endif
                ${ form[field](**field_args.get(field, {})) }
                % if helpers.get(field):
                    <i class="info-helper" title="${ helpers[field] }"></i>
                % endif
            </div>
        </div>
    % endfor
</div>

<script>
    $('#booked_for_user').on('change', function() {
        var user = JSON.parse($(this).val())[0];
        if (user) {
            $('#contact_email').val(user.email);
            $('#contact_phone').val(user.phone);
        }
    });

    % if not reservation:
        $('#booked_for_user').trigger('change');
    % endif
</script>
