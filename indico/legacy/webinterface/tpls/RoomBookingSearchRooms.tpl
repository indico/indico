<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
  <!-- Choose Button -->
  <div id="chooseButtonHelp" class="tip">
    <span>${ _('Black</span> - rooms that <b>do not</b> require confirmation') }<br/>
    <span class="moderatedRoom">${ _('Orange</span> - rooms that <b>require confirmation') }</b><br />
    <span class="privateRoom">${ _('Red</span> - rooms not publically bookable') }<br />
  </div>
  <!-- Free Search -->
  <div id="freeSearchHelp" class="tip">
    ${ _('Type in anything you remember about the room, i.e.') }:
    <ul>
      <li class="tip-no-borders"> ${ _('building or room number') }</li>
      <li class="tip-no-borders"> ${ _('person responsible') }</li>
      <li class="tip-no-borders"> ${ _('part of comment') }</li>
      <li class="tip-no-borders"> ${ _('equipment') }</li>
      <li class="tip-no-borders"> ${ _('room site') }</li>
      <li class="tip-no-borders"> ${ _('telephone') }</li>
      <li class="tip-no-borders">...</li>
    </ul>
    ${ _('Results will include rooms that have at least one of the specified words somewhere in description.') }
    <br />
    ${ _('Examples') }:
    <ul>
      <li class="tip-no-borders">Hauser&nbsp;(${ _('name of person responsible') })</li>
      <li class="tip-no-borders">513- 31- 28-&nbsp;(${ _('buildings') })</li>
      <li class="tip-no-borders">-006 -C19&nbsp;(${ _('rooms') })</li>
      <li class="tip-no-borders">prevessin&nbsp;(${ _('site') })</li>
    </ul>
      ${ _('Searching is case-insensitive and concerns all room\'s attributes.') }
  </div>
  <!-- Capacity -->
  <div id="capacityHelp" class="tip">
    <p class="tip-no-borders">
      ${ _("""Find only rooms having capacity within 20% range.
           In example for capacity = 20, rooms having capacity 16 - 24
           will be included in searching results.""") }<br />
    </p>
    <p class="tip-no-borders">
      ${ _("""If there are no rooms of capacity within 20% range,
           system will search for greater capacity.""") }
    </p>
    <p class="tip-no-borders">
      ${ _("""Example: for capacity equal 1, system will try to find rooms for
           only one person. This of course fails, so it will
           return rooms with capacity greater than 1.""") }
    </p>
  </div>
  <!-- Availability -->
  <div id="availabilityHelp" class="tip">
    <ul>
      <li class="tip-no-borders">
        ${ _('Available - the room must be available in the <b>whole</b> period') }
      </li>
      <li class="tip-no-borders">
        ${ _('Booked - the room must be booked <b>any time</b> in the period') }
      </li>
      <li class="tip-no-borders">
        ${ _('Don\'t care - room\'s availability is not checked') }
      </li>
    </ul>
  </div>
  <%include file="CHBookingRepetition.tpl"/>
</div>
<!-- END OF CONTEXT HELP DIVS -->


<h2 class="page-title">
    ${ _('Search rooms') }
</h2>

<%include file="ErrorList.tpl" args='errors=form.error_list, msg=_("There are some errors in the data you submitted")'/>

<!-- Choose a room -->
<h2 class="group-title">
    <i class="icon-location"></i>
    ${ _('Check a room') }
</h2>
<select name="roomName" id="roomName">
    % for room in rooms:
        <option value="${ url_for('rooms.roomBooking-roomDetails', room) }" class="${ room.kind }">
            ${ u'{}: &nbsp; {}'.format(room.location_name, room.full_name) }
        </option>
    % endfor
</select>

<input class="i-button highlight" type="button" value="${ _('Go to room') }" onclick="location.href = $('#roomName').val(); return false;"/>
${ contextHelp('chooseButtonHelp') }

<!-- Search for rooms -->
<div id="searchRooms">
    <form id="searchRoomsForm" method="post" action="">
        ${ form.csrf_token() }
        ${ form.start_dt() }
        ${ form.end_dt() }
        <h2 class="group-title">
            <i class="icon-search"></i>
            ${ _('Search for a room') }
        </h2>

        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <!-- LOCATION -->
            <tr>
                <td class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat">${ _('Location') }</span>
                </td>
                <td>
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                ${ form.location() }
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- FREE TEXT -->
            <tr>
                <td class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat">${ _('Room details') }</span>
                </td>
                <td>
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                ${ form.details(size=30) }
                                ${ contextHelp('freeSearchHelp') }
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- AVAILABILITY -->
            <tr>
                <td class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat"> ${ _('Availability') }</span>
                </td>
                <td>
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                ${ form.available(label_args={'style': 'font-weight: normal;'}) }
                                ${ contextHelp('availabilityHelp') }
                            </td>
                        </tr>
                        <%include file="RoomBookingPeriodFormOld.tpl"/>
                        <tr id='includePrebookingsTR'>
                            <td class="subFieldWidth" align="right" >
                                <small> ${ _('PRE-Bookings') }</small>
                            </td>
                            <td align="left" class="blacktext">
                                ${ form.include_pre_bookings() }
                                ${ form.include_pre_bookings.label(style='font-weight: normal;') }
                                ${ inlineContextHelp(_('Check if you want to avoid conflicts with PRE-bookings. By default conflicts are checked only against confirmed bookings.')) }
                            </td>
                        </tr>
                        <tr id='includePendingBlockingsTR'>
                            <td class="subFieldWidth" align="right" >
                                <small>${ _('Blockings') }</small>
                            </td>
                            <td align="left" class="blacktext">
                                ${ form.include_pending_blockings() }
                                ${ form.include_pending_blockings.label(style='font-weight: normal;') }
                                ${ inlineContextHelp(_('Check if you want to avoid conflicts with pending blockings. By default conflicts are checked only against confirmed blockings.')) }
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- CAPACITY -->
            <tr>
                <td class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat">${ form.capacity.label(style='font-weight: normal;') }</span>
                </td>
                <td align="right">
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                ${ form.capacity(size=3) }
                                ${ _('seats') }
                                ${ contextHelp('capacityHelp') }
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <!-- REQUIRED EQUIPMENT -->
            <tr id="equipment-search">
                <td nowrap class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat">${ _("Required equipment") }</span>
                </td>
                <td align="right">
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                % for eq in form.available_equipment:
                                    <div class="${ 'js-location js-location-{}'.format(equipment_locations[int(eq.data)]) }">
                                        ${ eq() }
                                        ${ eq.label(style='font-weight: normal;') }
                                    </div>
                                % endfor
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <tr>
                <td nowrap class="titleCellTD" style="width: 125px;">
                    <span class="titleCellFormat">${ _('Special attributes') }</span>
                </td>
                <td align="right">
                    <table width="100%" cellspacing="4px">
                        <tr>
                            <td align="left" class="blacktext">
                                ${ form.is_only_public() }
                                ${ form.is_only_public.label(style='font-weight: normal;') }
                                ${ inlineContextHelp(_('Include only publically reservable rooms.')) }
                                <br>
                                ${ form.is_auto_confirm() }
                                ${ form.is_auto_confirm.label(style='font-weight: normal;') }
                                ${ inlineContextHelp(_('Include only rooms, where bookings are automatically confirmed. This is the case for most rooms.')) }
                                % if form.is_only_my_rooms:
                                    <br>
                                    ${ form.is_only_my_rooms() }
                                    ${ form.is_only_my_rooms.label(style='font-weight: normal;') }
                                    ${ inlineContextHelp(_('Include only rooms you are responsible for.')) }
                                % endif
                                % if form.is_only_active:
                                    <br>
                                    ${ form.is_only_active() }
                                    ${ form.is_only_active.label(style='font-weight: normal;') }
                                    ${ inlineContextHelp(_('Include only active rooms. <b>This should be checked.</b> Please note that inactive rooms are considered deleted.')) }
                                % endif
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>

            <tr>
                <td colspan="2" style="padding-left:20px">
                    <button type="send" class="i-button highlight">
                        <i class="icon-search"></i>
                        ${ _('Search') }
                    </button>
                </td>
            </tr>
        </table>
    </form>
</div>

<script type="text/javascript">

    // Displays div with dates and hours
    function display_availability(bool) {
        $('#sdatesTR, #edatesTR, #hoursTR, #repTypeTR, #includePrebookingsTR, #includePendingBlockingsTR').toggle(bool);
    }
    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid(onSubmit) {
        if (onSubmit != true) {
            onSubmit = false;
        }

        // Clean up - make all textboxes white again
        var searchForm = $('#searchRoomsForm');
        $(':input', searchForm).removeClass('invalid');
        // Init
        var isValid = true;

        // Simple search -------------------------------------
        // Availability
        if ($('input[name="available"]:checked', searchForm).val() != '-1') { // only if NOT "Don't care"
            // validate_period is not defined, wth, apparently the old if condition was never net
            // isValid = validate_period();
        }
        // capacity
        if ($('#capacity').val().length > 0 && parseInt($('#capacity').val(), 10).toString() == 'NaN') {
            $('#capacity').addClass('invalid');
            isValid = false;
        }

        // Holidays warning
        if (isValid && !onSubmit) {
            var lastDateInfo = searchForm.data('lastDateInfo');
            var dateInfo = $('#sDay, #sMonth, #sYear, #eDay, #eMonth, #eYear').serialize();
            if (dateInfo != lastDateInfo) {
                searchForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource('roomBooking.getDateWarning', searchForm.serializeObject());

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $E('holidays-warning').set(holidaysWarning.get());
                    }
                });
            }
        }

        if (!$('#sdate').val()) {
            $('#sdate').addClass('invalid');
            isValid = false;
        }

        if (!$('#edate').val()) {
            $('#edate').addClass('invalid');
            isValid = false;
        }

        return isValid;
    }


    $(window).on('load', function() {
        $('#searchRoomsForm').on('keyup change', ':input', function() {
            forms_are_valid();
        }).on('submit', function(e) {
            if (!forms_are_valid(true)) {
                e.preventDefault();
                new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
            }
        });

        if (forms_are_valid()) {
            set_repeatition_comment();
        }
        $('#searchRoomsForm input[name="available"]').change(function() {
            display_availability(this.value != '-1');
        });
        display_availability($('input[name="available"]:checked').val() != '-1');
        $('#freeSearch').focus();
    });

    $('#location').on('change', function() {
        var locationId = $(this).val();
        $('#equipment-search').toggle(locationId != '__None')
        $('.js-location').hide().find('input:checkbox').prop('checked', false);
        $('.js-location-' + locationId).show();
    }).trigger('change');

</script>
