<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <li><span>${ _('Specify Search Criteria') }</span></li>
    <li><span>${ _('Select Available Period') }</span></li>
    <li><span class="current">${ _('Confirm Reservation') }</span></li>
</ul>


% if errors:
    <div class="error-message-box">
        <div class="message-text">
            ${ _("There are some errors:") }
            <ul>
                % for error in errors:
                    <li>${ error }</li>
                % endfor
            </ul>
        </div>
    </div>
% endif


<h2 class="group-title">
    <i class="icon-location"></i>
    ${ _('Room Details') }
</h2>

<%include file="RoomBookingRoomMiniDetails.tpl" args="room=room, booking_mode=True"/>


<h2 class="group-title">
    <i class="icon-calendar"></i>
    ${ _('Booking Time & Date') }
</h2>

<table>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Type")}
        </td>
        <td align="left" class="blacktext" id="typeInfo">
            ${ repeat_msg }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Start date")}
        </td>
        <td align="left" class="blacktext">
            ${ formatDate(start_dt) }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("End date")}
        </td>
        <td align="left" class="blacktext">
            ${ formatDate(end_dt) }
        </td>
    </tr>
    <tr>
        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
            ${ _("Time")}
        </td>
        <td align="left" class="blacktext">
            ${ formatTime(start_dt) } - ${ formatTime(end_dt) }
        </td>
    </tr>
</table>

<form method="POST" id="bookForm">
    <input type="hidden" name="step" value="3">
    ${ form.start_date(type='hidden') }
    ${ form.end_date(type='hidden') }
    ${ form.repeat_unit(type='hidden') }
    ${ form.repeat_step(type='hidden') }
    ${ form.room_id(type='hidden') }

    <h2 class="group-title">
        <i class="icon-user"></i>
        ${ _('Being Booked For') }
    </h2>

    <table>
        <%
            fields = ['booked_for_id', 'contact_email', 'contact_phone', 'booking_reason']
            field_args = {
                'contact_email': {'style': 'width: 240px;'},
                'contact_phone': {'style': 'width: 240px;'},
                'booking_reason': {'rows': 3, 'cols': 50}
            }
        %>
        % for field in fields:
            <tr>
                <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                    ${ form[field].label.text }
                </td>
                <td align="left" class="blacktext">
                    ${ form[field](**field_args.get(field, {})) }
                    % if field == 'booked_for_id':
                        ${ form.booked_for_name(readonly=True, style='width: 240px;') }
                        <input type="button" value="${ _('Search') }" id="searchUsers">
                    % endif
                    ${ contextHelp(field + '_help') }
                </td>
            </tr>
        % endfor
    </table>

    <h2 class="group-title">
        <i class="icon-projector"></i>
        ${ _('Collaboration & Assistance') }
    </h2>

    <table>
        <tr>
            <td style="vertical-align:top;">
                ${ form.needs_general_assistance() }
            </td>
            <td style="width: 100%; padding-left: 3px;">
                ${ form.needs_general_assistance.label(style='font-weight: normal;') }
            </td>
        </tr>
        <% eq_list = list(form.equipments) %>
        % if eq_list:
            <tr>
                <td style="vertical-align:top;">
                    ${ form.uses_video_conference() }
                </td>
                <td style="width: 100%; padding-left: 3px;">
                    ${ form.uses_video_conference.label(style='font-weight: normal;') }
                    ${ contextHelp('iWillUseVideoConferencingHelp') }
                </td>
            </tr>
            % for subfield in [form.needs_video_conference_setup] + eq_list:
                <tr class="js-vc-row">
                    <td style="vertical-align:top;"></td>
                    <td style="width: 100%; padding-left: 3px;">
                        ${ subfield() }
                        ${ subfield.label(style='font-weight: normal;') }
                    </td>
                </tr>
            % endfor
        % endif
    </table>

    <h2 class="group-title"></h2>
    <div>
        % if form.submit_prebook:
            ${ form.submit_prebook(class_='i-button highlight') }
        % endif
        % if form.submit_book:
            ${ form.submit_book(class_='i-button highlight') }
        % endif
        ${ form.skip_conflicts() } ${ form.skip_conflicts.label() }
    </div>
</form>


<script>
    $('#searchUsers').on('click', function() {
        new ChooseUsersPopup(
            $T('Select a user'),
            true,
            null, false,
            true, null,
            true, true, false,
            function(users) {
                $('#booked_for_name').val(users[0].name);
                $('#booked_for_id').val(users[0].id);
                $('#contact_email').val(users[0].email);
                $('#telephone').val(users[0].phone);
            }
        ).execute();
    });

    $('#uses_video_conference').on('change', function() {
        $('.js-vc-row input:checkbox').prop('disabled', !this.checked);
        if (!this.checked) {
            $('.js-vc-row input:checkbox').prop('checked', false);
        }
    }).trigger('change');

    var validating = false;

    function validateForm() {
        var isValid = true;
        $('#contact_email, #booking_reason').each(function() {
            var $this = $(this);
            var valid = !!$this.val().trim();
            isValid = isValid && valid;
            $this.toggleClass('hasError', !valid);
        });
        if ($('#uses_video_conference').length) {
            var vcEnabled = $('#uses_video_conference').prop('checked');
            var vcErrors = vcEnabled != !!$('.js-vc-row input:not(#needs_video_conference_setup):checked').length;
            var vcLabel = $('label[for="uses_video_conference"]');
            vcLabel.toggleClass('text-error', vcErrors);
            if (vcErrors) {
                vcLabel.attr('title', 'You need to select at least one piece of Video Conference equipment');
            }
            else {
                vcLabel.qtip('destroy', true).removeAttr('title');
            }
            isValid = isValid && !vcErrors;
        }
        return isValid;
    }

    $('#bookForm :input').on('input change', function() {
        if (validating) {
            validateForm();
        }
    });

    $('#bookForm').on('submit', function(e) {
        validating = true;
        if (!validateForm()) {
            e.preventDefault();
        }
    });
</script>


<div id="tooltipPool" style="display: none">
    <div id="booked_for_id_help" class="tip">
        ${ _("<b>Required.</b> For whom the booking is made.") }
    </div>
    <div id="contact_email_help" class="tip">
        ${ _("'<b>Required.</b> Contact email. You can specify more than one email address by separating them with commas, semicolons or whitespaces.") }
    </div>
    <div id="contact_phone_help" class="tip">
        ${ _("Contact telephone") }
    </div>
    <div id="booking_reason_help" class="tip">
        ${ _("<b>Required.</b> The justification for booking. Why do you need this room?") }
    </div>
    <div id="whereIsKeyHelp" class="tip">
        ${ _('How to obtain a key.') }
    </div>
    <div id="skipConflictsHelp" class="tip">
        ${ _('Creates or saves your booking only for available dates. All conflicting days will be excluded.') }
    </div>
    <div id="iWillUseVideoConferencingHelp" class="tip">
        ${ _('<strong>Only</strong> check this if you are actually going to use it!') }
    </div>
</div>
