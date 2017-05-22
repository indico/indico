<% from indico.modules.rb import rb_settings %>

<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none;">
    <div id="nameCH" class="tip">
        ${ _('If you live it blank, system will auto generate "building-floor-room" name.') } <br/>
    </div>
    <div id="siteCH" class="tip">
        <b> ${ _('Required.') }</b>
    </div>
    <div id="buildingCH" class="tip">
        <b> ${ _('Required.') }</b> ${ _('Must be a positive number.') }<br/>
    </div>
    <div id="floorCH" class="tip">
        <b> ${ _('Required.') }</b>
    </div>
    <div id="roomCH" class="tip">
        <b> ${ _('Required.') }</b>  ${ _('Room number.') }
    </div>
    <div id="latitudeCH" class="tip">
        <b> ${ _('Latitude.') } </b>
    </div>
    <div id="longitudeCH" class="tip">
        <b> ${ _('Longitude.') } </b>
    </div>
    <div id="is_activeCH" class="tip">
        ${ _("Whether the room exists. Turn it off if room is no longer suitable for meetings, but for some reason you don't want to delete it.") }
    </div>
    <div id="is_reservableCH" class="tip">
        ${ _("Whether the room is bookable by anyone having a user account.") }
    </div>
    <div id="reservations_need_confirmationCH" class="tip">
        ${ _("Whether bookings must be accepted by person responsible.") }
    </div>
    <div id="notification_before_daysCH" class="tip">
        ${ _("Send booking reminders X days before the start of a single-occurrence or daily booking (leave empty to use default)")  }
    </div>
    <div id="notification_before_days_weeklyCH" class="tip">
        ${ _("Send booking reminders X days before an occurrence of a weekly booking (leave empty to use default)")  }
    </div>
    <div id="notification_before_days_monthlyCH" class="tip">
        ${ _("Send booking reminders X days before an occurrence of a monthly booking (leave empty to use default)")  }
    </div>
    <div id="notification_for_assistanceCH" class="tip">
        ${ _("Send notifications asking for assistance with room setup") }
    </div>
    <div id="notifications_enabledCH" class="tip">
        ${ _("Enable/disable reminders for this room") }
    </div>
    <div id="booking_limit_daysCH" class="tip">
        ${ _("Maximum number of days a booking for this room may last") }
    </div>
    <div id="key_locationCH" class="tip">
        ${ _("How to obtain a key. Typically a phone number.") }
    </div>
    <div id="ownerCH" class="tip">
        <b> ${ _('Required.') }</b>  ${ _('Person who is responsible for the room.') } <br/>
        ${ _('This person will receive notifications and is able to reject bookings.') }
    </div>
    <div id="telephoneCH" class="tip">
        ${ _('Room\'s telephone.') }
    </div>
    <div id="capacityCH" class="tip">
        <b> ${ _('Required.') }</b>  ${ _('Must be a positive number.') }
    </div>
    <div id="divisionCH" class="tip">??!</div>
    <div id="surface_areaCH" class="tip">
        ${ _('Surface in square meters. Must be a positive number.') }
    </div>
    <div id="max_advance_daysCH" class="tip">
        <b> ${ _('Maximum number of days the room can be booked in advance. Must be a positive number (or empty for no restriction).') }</b>
    </div>
    <div id="commentsCH" class="tip">
        ${ _('Any other comments - recommended.') }
    </div>
    <div id="photoCH" class="tip">
        <b> ${ _('WARNING - PLEASE READ.') }</b><br/>
        <ul>
            <li> ${ _('Either you upload two photos (large and small) or none.') }</li>
            <li> ${ _('Small photo must be 90x60 pixels.') }</li>
            <li> ${ _('Large photo may be of any size.') }</li>
        </ul>
    </div>
    <div id="delete_photosCH" class="tip">
        ${ _('Deletes the current photos. Not necessary if you just want to replace them; the old ones are deleted automatically in this case.') }
    </div>
    <div id="dailyBookablePeriodsCH" class="tip">
        ${ _('Time format: \'HH:MM\'') }
    </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<form action="" method="post" enctype="multipart/form-data">
    ${ form.csrf_token() }
    <table width="95%" cellpadding="0" cellspacing="0" border="0" align="center">
        <tr>
            <td class="formTitle">
                <a href="${ url_for('rooms_admin.roomBooking-adminLocation', location) }">
                    &lt;&lt;${ _('Back') }
                </a>
            </td>
        </tr>
        <tr>
            <td>
                <span class="formTitle" style="border-bottom-width: 0px">
                    % if room.id is None:
                        ${ _('New Room') }
                    % else:
                        ${ _('Modify Room') }
                    % endif
                </span>
                <br/>
                % if errors:
                    <br>
                    <span style="color: Red; margin-left: 6px;">
                      ${ ngettext('Saving failed. There is an error', 'Saving failed. There are {0} errors', len(errors)).format(len(errors)) }:
                    </span>
                    <ul>
                        % for error in errors:
                            <li>${ error }</li>
                        % endfor
                    </ul>
                % endif
                <br><br>
                <table width="90%" align="center" border="0">
                    <!-- LOCATION -->
                    <tr>
                        <td width="24%" class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _('Location') }</span>
                        </td>
                        <td width="76%">
                            <table width="100%">
                                <tr>
                                    <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                                        <small>${ _('Location') }</small>
                                    </td>
                                    <td align="left" class="blacktext">
                                        ${ location.name }
                                    </td>
                                </tr>
                                % for field in ['name', 'site', 'building', 'floor', 'number', 'longitude', 'latitude']:
                                    <tr>
                                        <td class="subFieldWidth" align="right" valign="top"
                                            style="padding-right: 5px;">
                                            <small>${ form[field].label.text }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            ${ form[field]() } ${ contextHelp(field + 'CH') }
                                        </td>
                                    </tr>
                                % endfor
                            </table>
                        </td>
                        <td>&nbsp;</td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- OPTIONS -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _('Options')}</span>
                        </td>
                        <td colspan="2">
                            <table>
                                <%
                                    fields = ['is_active', 'is_reservable', 'reservations_need_confirmation',
                                              'notification_for_assistance', 'notification_before_days',
                                              'notification_before_days_weekly', 'notification_before_days_monthly',
                                              'notifications_enabled', 'booking_limit_days']
                                    reminder_fields = {'notification_before_days', 'notification_before_days_weekly',
                                                       'notification_before_days_monthly', 'notifications_enabled'}
                                    field_args = {
                                        'notification_before_days': dict(style='width: 25px;', maxlength=2),
                                        'notification_before_days_weekly': dict(style='width: 25px;', maxlength=2),
                                        'notification_before_days_monthly': dict(style='width: 25px;', maxlength=2),
                                        'booking_limit_days': dict(style='width: 40px;',
                                                                   placeholder=rb_settings.get('booking_limit'))
                                    }
                                %>
                                % for field in fields:
                                    <tr>
                                        <td class="subFieldWidth" align="right" valign="top"
                                            style="padding-right: 5px;">
                                            <small>${ form[field].label.text }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            % if field in reminder_fields and not rb_settings.get('notifications_enabled', True):
                                                ${ form[field](disabled=True, **field_args.get(field, {})) }
                                            % else:
                                                ${ form[field](**field_args.get(field, {})) }
                                            % endif
                                            ${ contextHelp(field + 'CH') }
                                        </td>
                                    </tr>
                                % endfor
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- CONTACT -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _("Contact")}</span>
                        </td>
                        <td colspan="2">
                            <table>
                                % for field in ['owner', 'key_location', 'telephone']:
                                    <tr>
                                        <td align="right" valign="top" style="padding-right: 5px;">
                                            <small>${ form[field].label.text }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            ${ form[field]() }
                                            ${ contextHelp(field + 'CH') }
                                        </td>
                                    </tr>
                                % endfor
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- PHOTO -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _('Photo') }</span>
                        </td>
                        <td colspan="2">
                            <table>
                                % if room.photo_id:
                                    <tr>
                                        <td align="right" valign="top" style="padding-right: 5px;">
                                            <small>${ form.delete_photos.label.text }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            ${ form.delete_photos() }
                                            ${ contextHelp('delete_photosCH') }
                                        </td>
                                    </tr>
                                % endif
                                <tr>
                                    <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                                        <small>${ form.large_photo.label.text }</small>
                                    </td>
                                    <td align="left" class="blacktext">
                                        ${ form.large_photo() } ${ contextHelp('photoCH' ) }
                                    </td>
                                </tr>
                                <tr>
                                    <td align="right" valign="top" style="padding-right: 5px;">
                                        <small>${ form.small_photo.label.text }</small>
                                    </td>
                                    <td align="left" class="blacktext">
                                        ${ form.small_photo() }
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- INFORMATION -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _('Information') }</span>
                        </td>
                        <td colspan="2">
                            <table width="100%">
                                <%
                                    fields = ['capacity', 'division', 'surface_area', 'max_advance_days', 'comments']
                                    field_after = {
                                        'capacity': _('seats'),
                                        'surface_area': _('m<sup>2</sup>'),
                                        'max_advance_days': _('days'),
                                    }
                                    field_args = {
                                        'comments': {'cols': 40},
                                        'max_advance_days': {'size': 10}
                                    }
                                %>
                                % for field in fields:
                                    <tr>
                                        <td class="subFieldWidth" align="right" valign="top" style="padding-right: 5px;">
                                            <small>${ form[field].label.text }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            ${ form[field](**field_args.get(field, {})) }
                                            ${ field_after.get(field, '') }
                                            ${ contextHelp(field + 'CH') if field != 'division' else '' }
                                        </td>
                                    </tr>
                                % endfor
                                <tr>
                                    <td align="right" valign="top" style="padding-right: 5px;">
                                        <small>${ _('Unavailable booking periods') }</small>
                                    </td>
                                    <td align="left" class="blacktext">
                                        <table id="nonBookablePeriodsTable">
                                            % for subform in form.nonbookable_periods:
                                                <% index = loop.index %>
                                                <tr class="startEndDate">
                                                    % for field in ['start', 'end']:
                                                        <td class="startEndDateEntry">${ subform[field].label.text }</td>
                                                        <td id="${ field }DateNonBookablePeriod${ index }">${ subform[field]() }</td>
                                                    % endfor
                                                    % if loop.first:
                                                        <td>
                                                            <span onclick="addNonBookablePeriod()">
                                                                <a class="fakeLink">${ _('add period') }</a>
                                                            </span>
                                                        </td>
                                                    % endif
                                                </tr>
                                            % endfor
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="right" valign="top" style="padding-right: 5px;">
                                        <small>${ _('Daily availability periods') }</small>
                                    </td>
                                    <td align="left" class="blacktext">
                                        <table id="dailyBookablePeriodsTable">
                                            % for subform in form.bookable_hours:
                                                <tr class="startEndDate">
                                                    % for field in ['start', 'end']:
                                                        <td class="startEndDateEntry">${ subform[field].label.text }</td>
                                                        <td>${ subform[field](style='width: 50px;') }</td>
                                                    % endfor
                                                    % if loop.first:
                                                        <td>
                                                            ${ contextHelp('dailyBookablePeriodsCH') }
                                                            <span onclick="addDailyBookablePeriod()">
                                                                <a class="fakeLink">${ _('add period') }</a>
                                                            </span>
                                                        </td>
                                                    % endif
                                                </tr>
                                            % endfor
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- CUSTOM ATTRIBUTES -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat"> ${ _('Custom attributes') }</span>
                        </td>
                        <td colspan="2">
                            % if form._attribute_fields:
                                <table width="100%">
                                    % for field in form._attribute_fields:
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"
                                                style="padding-right: 5px;">
                                                <small>${ field.label.text }</small>
                                            </td>
                                            <td align="left" class="blacktext">
                                                ${ field() }
                                                % if field.label.text.lower() == 'notification email':
                                                    % if field.flags.required:
                                                        ${ inlineContextHelp('<b>Required.</b> You can specify more than one email address separated by commas.') }
                                                    % else:
                                                        ${ inlineContextHelp('You can specify more than one email address separated by commas.') }
                                                    % endif
                                                % elif field.flags.required:
                                                    ${ inlineContextHelp('<b>Required.</b>') }
                                                % endif
                                            </td>
                                        </tr>
                                    % endfor
                                </table>
                            % else:
                                ${ _('There are no custom attributes to pick.') }
                                <a href="${ url_for('rooms_admin.roomBooking-adminLocation', location) }">${ _('You may first add some to location, {0}.').format(location.name) }</a>
                            % endif
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- EQUIPMENT -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat">${ _('Equipment') }</span>
                        </td>
                        <td colspan="2">
                            <% eq_list = list(form.available_equipment) %>
                            % if eq_list:
                                <table width="100%">
                                    <tr>
                                        <td class="subFieldWidth" align="right" valign="top"
                                            style="padding-right: 5px;">
                                            <small>${ _('Room has') }</small>
                                        </td>
                                        <td align="left" class="blacktext">
                                            % for eq in eq_list:
                                                ${ eq() } ${ eq.label() }<br>
                                            % endfor
                                        </td>
                                    </tr>
                                </table>
                            % else:
                                ${ _('There is no equipment to pick.') }
                                <a href="${ url_for('rooms_admin.roomBooking-adminLocation', location) }">${ _('You may add some to location, {0}.').format(location.name) }</a>
                            % endif
                        </td>
                    </tr>
                    <tr>
                        <td>&nbsp;</td>
                    </tr>
                    <!-- ACTIONS -->
                    <tr>
                        <td class="titleUpCellTD" style="vertical-align: top;">
                            <span class="titleCellFormat"> ${ _('Actions') }</span>
                        </td>
                        <td colspan="2">
                            <input style="margin-left: 18px;" type="submit" class="i-button" value="${ _('Save') }"/>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>

<script>
    var nbpStartLabel = $('#nonBookablePeriodsTable tr:eq(0) .startEndDateEntry:eq(0)').text();
    var nbpEndLabel = $('#nonBookablePeriodsTable tr:eq(0) .startEndDateEntry:eq(1)').text();
    var btStartLabel = $('#dailyBookablePeriodsTable tr:eq(0) .startEndDateEntry:eq(0)').text();
    var btEndLabel = $('#dailyBookablePeriodsTable tr:eq(0) .startEndDateEntry:eq(1)').text();

    $('#nonBookablePeriodsTable tr').each(function(i) {
        var startDate = $('input', this).eq(0).val();
        var endDate = $('input', this).eq(1).val();
        var startDateField = IndicoUI.Widgets.Generic.dateField(true, {
            id: 'nonbookable_periods-{0}-start'.format(i),
            name: 'nonbookable_periods-{0}-start'.format(i)
        });
        var endDateField = IndicoUI.Widgets.Generic.dateField(true, {
            id: 'nonbookable_periods-{0}-end'.format(i),
            name: 'nonbookable_periods-{0}-end'.format(i)
        });

        $E('startDateNonBookablePeriod' + i).set(startDateField);
        $E('endDateNonBookablePeriod' + i).set(endDateField);

        startDateField.set(startDate);
        endDateField.set(endDate);

        if (i == 0) {
            nbpStartLabel = $('.startEndDateEntry', this).eq(0).text();
            nbpEndLabel = $('.startEndDateEntry', this).eq(1).text();
        }
    });

    function addNonBookablePeriod() {
        var i = $('#nonBookablePeriodsTable tr').length;
        $('#nonBookablePeriodsTable tbody').append(
            '<tr class="startEndDate"> \
                <td class="startEndDateEntry">{0}</td> \
                <td id="startDateNonBookablePeriod{2}"></td> \
                <td class="startEndDateEntry">{1}</td> \
                <td id="endDateNonBookablePeriod{2}"></td> \
            </tr>'.format(nbpStartLabel, nbpEndLabel, i)
        );

        $E('startDateNonBookablePeriod' + i).set(
            IndicoUI.Widgets.Generic.dateField(true, {
                id: 'nonbookable_periods-{0}-start'.format(i),
                name: 'nonbookable_periods-{0}-start'.format(i)
            })
        );
        $E('endDateNonBookablePeriod' + i).set(
            IndicoUI.Widgets.Generic.dateField(true, {
                id: 'nonbookable_periods-{0}-end'.format(i),
                name: 'nonbookable_periods-{0}-end'.format(i)
            })
        );
    }

    function addDailyBookablePeriod() {
        $('#dailyBookablePeriodsTable tbody').append(
            '<tr class="startEndDate"> \
                 <td class="startEndDateEntry">{0}</td> \
                 <td><input id="bookable_hours-{2}-start" name="bookable_hours-{2}-start" style="width: 50px;" type="time"></td> \
                 <td class="startEndDateEntry">{1}</td> \
                 <td><input id="bookable_hours-{2}-end" name="bookable_hours-{2}-end" style="width: 50px;" type="time"></td> \
            </tr>'.format(btStartLabel, btEndLabel, $('#dailyBookablePeriodsTable tr').length)
        );
    }
</script>
