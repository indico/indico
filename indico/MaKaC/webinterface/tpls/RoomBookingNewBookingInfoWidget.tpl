<%page args="form=None"/>

<%
    fields = ['booked_for_id', 'contact_email', 'contact_phone', 'booking_reason']
    field_args = {
        'booking_reason': {'rows': 3, 'placeholder': _('Reason...')}
    }
    helpers = {
        'contact_email': 'You can specify multiple email addresses separated by commas.',
        'booking_reason': 'Specify why you need this room.'
    }
%>

<div id="bookedForInfo">
    % for field in fields:
        <div class="toolbar thin">
            <div class="group">
                % if not form[field].label.text == "Reason":
                    <span class="i-button label heavy">
                        ${ form[field].label.text }
                    </span>
                % endif
                ${ form[field](**field_args.get(field, {})) }
                % if field == 'booked_for_id':
                    ${ form.booked_for_name(readonly=True) }
                    <input type="button" id="searchUsers" value="${ _('Search') }" class="i-button">
                % endif
                % if helpers.get(field):
                    <i class="info-helper" title="${ helpers[field] }"></i>
                % endif
            </div>
        </div>
    % endfor
</div>

<script>
    $(document).ready(function() {
        $('#booked_for_name, #searchUsers').on('click', function() {
            new ChooseUsersPopup(
                $T('Select a user'),
                true, null, false, true, null, true, true, false,
                function(users) {
                    $('#booked_for_name').val(users[0].name);
                    $('#booked_for_id').val(users[0].id);
                    $('#contact_email').val(users[0].email);
                    $('#telephone').val(users[0].phone);
                }
            ).execute();
        });
    });
</script>
