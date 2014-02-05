<script type="text/javascript">

    // Reds out the invalid textboxes and returns false if something is invalid.
    // Returns true if form may be submited.
    function forms_are_valid(onSubmit) {
        if (onSubmit != true) {
            onSubmit = false;
        }

        // Init, clean up (make all textboxes white again)
        var bookingForm = $('#bookingForm');
        $(':input', bookingForm).removeClass('invalid');


        // Holidays warning
        if (!onSubmit) {
            var lastDateInfo = bookingForm.data('lastDateInfo');
            var dateInfo = $('#sDay, #sMonth, #sYear, #eDay, #eMonth, #eYear').serialize();
            if (dateInfo != lastDateInfo) {
                bookingForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource('roomBooking.getDateWarning', bookingForm.serializeObject());

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $('#holidays-warning').html(holidaysWarning.get());
                        if (holidaysWarning.get() == '')
                            $('#holidays-warning').hide();
                        else
                            $('#holidays-warning').show();
                    }
                });
            }
        }

        var isValid = true;
        % if not infoBookingMode:
            // Date validator (repeatability)
            isValid = validate_period(true, ${allowPast}, 1, $('#repeatability').val()) && isValid; // 1: validate dates
            // Time validator
            isValid = validate_period(false, ${allowPast}, 2) && isValid; // 2: validate only times
        % endif
        required_fields(['bookedForName', 'contactEmail', 'reason']) && isValid;
        if (onSubmit) {
            isValid = required_fields(['bookedForName', 'contactEmail', 'reason']) && isValid;
        } else {
            isValid = required_fields(['bookedForName', 'contactEmail']) && isValid;
        }
        % if not infoBookingMode and not (user.isRBAdmin() or user.getId() == candResv.room.responsibleId) and candResv.room.maxAdvanceDays > 0:
            isValid = validate_allow(${candResv.room.maxAdvanceDays}) && isValid;
        % endif
        if (!Util.Validation.isEmailList($('#contactEmail').val())) {
            isValid = false;
            $('#contactEmail').addClass('invalid');
        }

        % if candResv.room.needsAVCSetup:
            var vcIsValid = true;
            if ($('#usesAVC').is(':checked')) {
                vcIsValid = $('input.videoConferenceOption').is(':checked');
            }
            $('#vcSystemList').toggleClass('invalid', !vcIsValid);
            isValid = isValid && vcIsValid;
        % endif

        return isValid;
    }

    function searchForUsers() {
            var popup = new ChooseUsersPopup($T('Select a user'),
                                         true,
                                         null, false,
                                         true, null,
                                         true, true, false,
                                         function(users) {
                                             $E('bookedForName').set(users[0].name);
                                             $E('bookedForId').set(users[0].id);
                                             $E('contactEmail').set(users[0].email);
                                             $E('contactPhone').set(users[0].phone);
                                         });

            popup.execute();
    }

    function isBookable() {
        // Get the room location and id in the SELECT
        var roomLocation = $("#roomName option:selected").data("location");
        var roomID = $("#roomName option:selected").data("id");

        // Send an asynchronous request to the server
        // Depending of result, either recheck the conflicts
        // Relaod Room Booking form or pop up a dialog
        indicoRequest('user.canBook',
            {roomLocation: roomLocation, roomID: roomID},
            function(result, error) {
                if(!error) {
                    if (result) {
                        $("#roomLocation").val(roomLocation);
                        $("#roomID").val(roomID);
                        $("#bookingForm").submit();
                    } else {
                        //bookButtonWrapper.set(bookButton);
                        var popup = new AlertPopup($T('Booking Not Allowed'),
                                $T("You're not allowed to book this room"));
                        popup.open();
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            });
    }

    function saveBooking() {
        $('#bookingForm').attr('action', '${saveBookingUH.getURL(conf)}');
        if (forms_are_valid(true))
            $('#bookingForm').submit();
        else
            new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
    }

    function checkBooking() {
        $('#bookingForm').attr('action', '${bookingFormURL.getURL(conf)}#conflicts');
        $('#bookingForm').submit();
    };

    $(window).on('load', function() {

        % if showErrors:
            var popup = new ExclusivePopupWithButtons($T('Booking failed'), function(){popup.close();}, false, false, true);

            popup._getButtons = function() {
                var self = this;
                return [
                    [$T('Change Search Criteria'), function() {
                        window.location='${ urlHandlers.UHRoomBookingBookRoom.getURL() }';
                        self.close();
                    }],
                    [$T('Close'), function() {
                        self.close();
                    }],
                ];
            }
            popup.draw = function(){
                var errorList = "";
                % for error in errors:
                    errorList +="${error}. ";
                % endfor
                var span1 = Html.span('', $T(errorList));
                return this.ExclusivePopupWithButtons.prototype.draw.call(this, Widget.block([span1, Html.br()]), {maxWidth: pixels(500)});
            };

            popup.open();
        % elif candResv.room.needsAVCSetup:
            $('.videoConferenceOption, #needsAVCSupport').change(function() {
                if(this.checked) {
                    $('#usesAVC').prop('checked', true);
                }
            });
            $('#usesAVC').change(function() {
                if(!this.checked) {
                    $('.videoConferenceOption, #needsAVCSupport').prop('checked', false);
                }
            });
        % endif

        $('#bookingForm').delegate(':input', 'keyup change', function() {
            if (forms_are_valid())
                % if not infoBookingMode:
                    updateTimeSlider();
                % endif
                ;
        }).submit(function(e) {
            if (!forms_are_valid()) {
                e.preventDefault();
                 new AlertPopup($T("Error"), $T("There are errors in the form. Please correct fields with red background.")).open();
            };
        }).keydown(function(e) {
            if(e.which == 13 && !$(e.target).is('textarea, :submit')) {
                e.preventDefault();
                saveBooking();
            }
        });

        if (forms_are_valid()) {
            set_repeatition_comment();
        }
    });
</script>

    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">
        <!-- Where is key? -->
        <div id="whereIsKeyHelp" class="tip">
             ${ _("How to obtain a key? Often just a phone number.")}
        </div>
        <div id="skipConflictsHelp" class="tip">
             ${ _("Creates or saves your booking only for available dates. All conflicting days will be excluded.")}
        </div>
        <div id="iWillUseVideoConferencing" class="tip">
             ${ _("Check <b>if</b> you are going to use video-conferencing equipment.")}<br />
        </div>
        <div id="iNeedAVCSupport" class="tip">
             ${ _("Check <b>if</b> you need AVC Support to help you with video-conferencing equipment.")}<br />
        </div>
        <%include file="CHBookingRepeatition.tpl"/>
    </div>
    <!-- END OF CONTEXT HELP DIVS -->

    <form id="bookingForm" name="bookingForm" action="${bookingFormURL.getURL(conf)}#" method="post">
    <input type="hidden" id="afterCalPreview" name="afterCalPreview" value="True" />

    <table style="width: 100%; padding-left: 20px;">
    % if standalone:
        <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
        </tr>
    % endif
        <tr>
            <td>
                <input type="hidden" name="roomID" id="roomID" value="${candResv.room.id}" />
                <input type="hidden" name="roomLocation" id="roomLocation" value="${candResv.room.locationName}" />
                <input type="hidden" name="finishDate" id="finishDate"  />
                <input type="hidden" value="${ startDT.day }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ startDT.month }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ startDT.year }" name="sYear" id="sYear"/>
                <input type="hidden" value="${ endDT.day }" name="eDay" id="eDay"/>
                <input type="hidden" value="${ endDT.month }" name="eMonth" id="eMonth"/>
                <input type="hidden" value="${ endDT.year }" name="eYear" id="eYear"/>
                % if infoBookingMode:
                    <input type="hidden" value="${ startT }" name="sTime" id="sTime"/>
                    <input type="hidden" value="${ endT }" name="eTime" id="eTime"/>
                    <ul id="breadcrumbs" style="margin:0px 0px 0px -15px; padding: 0; list-style: none;">
                        <li><span><a href="${ urlHandlers.UHRoomBookingBookRoom.getURL() }">${_("Specify Search Criteria")}</a></span></li>
                        <li><span><a href="${ url_for('rooms.roomBooking-bookingListForBooking', fromSession=1) }">${_("Select Available Period")}</a></span></li>
                        <li><span class="current">${_("Confirm Reservation")}</span></li>
                    </ul>
                % elif formMode == FormMode.NEW:
                    <span class="groupTitle bookingTitle" style="border-bottom-width: 0px; font-weight: bold">
                         ${ _("New")}&nbsp;${bookingMessage}ing
                    </span>
                % endif
                % if formMode == FormMode.MODIF:
                    <span class="groupTitle bookingTitle" style="border-bottom-width: 0px; font-weight: bold">
                     ${ _("Modify")}&nbsp;${bookingMessage}ing
                    <input type="hidden" name="resvID" id="resvID" value="${candResv.id}" />
                    </span>
                % endif
                <table width="100%" align="left" border="0">
                  <%include file="RoomBookingRoomMiniDetails.tpl" args="room = candResv.room "/>
                  <tr>
                    <td>
                        <div class="groupTitle bookingTitle">${'Booking Time & Date'}</div>
                    </td>
                  </tr>
                  <!-- BOOKING TIME & DATE -->
                  <tr>
                    <td>
                        <table id="roomBookingTable">
                            <%include file="RoomBookingPeriodForm.tpl" args="repeatability = candResv.repeatability, form = 0, unavailableDates = candResv.room.getNonBookableDates(skipPast=True), availableDayPeriods = candResv.room.getDailyBookablePeriods(), maxAdvanceDays = candResv.room.maxAdvanceDays"/>
                        </table>
                    </td>
                </tr>
                % if not infoBookingMode:
                    <tr>
                        <td id="conflicts" colspan="2">
                            ${ roomBookingRoomCalendar }
                        </td>
                    </tr>
                % endif
                <!-- BOOKED FOR -->
                <tr>
                    <td>
                        <div class="groupTitle bookingTitle">${'Being Booked For'}</div>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table width="100%">
                            % if rh._requireRealUsers:
                                <tr>
                                    <td class="subFieldWidth" align="right" valign="top">
                                         ${ _("User")}&nbsp;&nbsp;
                                    </td>
                                    <td align="left" class="blacktext">
                                        <input type="hidden" id="bookedForId" name="bookedForId" value="${ candResv.bookedForId or '' }" />
                                        <input type="text" id="bookedForName" name="bookedForName" style="width: 240px;" value="${ candResv.bookedForUser.getFullName() if candResv.bookedForId else candResv.bookedForName }" onclick="searchForUsers();" readonly="readonly" />
                                        <input type="button" value="Search" onclick="searchForUsers();" />
                                        ${ inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) }
                                    </td>
                                </tr>
                            % else:
                                <tr>
                                    <td class="subFieldWidth" align="right" valign="top">
                                        ${ _("Name")}&nbsp;&nbsp;
                                    </td>
                                    <td align="left" class="blacktext">
                                        <input type="text" id="bookedForName" name="bookedForName" style="width: 240px;" value="${ verbose( candResv.bookedForName ) }" />
                                        ${ inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) }
                                    </td>
                                </tr>
                            % endif
                            <tr>
                                <td class="subFieldWidth" align="right" valign="top">
                                    ${ _("E-mail")}&nbsp;&nbsp;
                                </td>
                                <td align="left" class="blacktext">
                                    <input type="text" id="contactEmail" name="contactEmail" style="width: 240px;" value="${ verbose( candResv.contactEmail )}" />
                                    ${inlineContextHelp('<b>Required.</b> Contact email. You can specify more than one email address by separating them with commas, semicolons or whitespaces.' )}
                                </td>
                            </tr>
                            <tr>
                                <td align="right" class="subFieldWidth" valign="top">
                                    ${ _("Telephone")}&nbsp;&nbsp;
                                </td>
                                <td align="left" class="blacktext">
                                    <input type="text" id="contactPhone" name="contactPhone" style="width: 240px;" value="${ verbose( candResv.contactPhone ) }" />
                                    ${inlineContextHelp('Contact telephone.' )}
                                </td>
                            </tr>
                            <tr>
                                <td align="right" class="subFieldWidth" valign="top">
                                    ${ _("Reason")}&nbsp;&nbsp;
                                </td>
                                <td align="left" class="blacktext">
                                    <textarea rows="3" cols="50" id="reason" name="reason" >${ verbose( candResv.reason ) }</textarea>
                                    ${inlineContextHelp(_("<b>Required.</b> The justification for booking. Why do you need this room?"))}
                                </td>
                            </tr>
                            % if candResv.room.needsAVCSetup:
                                <tr>
                                    <td align="right" class="subFieldWidth" valign="top">
                                        <span style="color: Red;">${ _("I will use video-conf. equipment (please only check that which you need)")}</span>&nbsp;&nbsp;
                                    </td>
                                    <td align="left" class="blacktext">
                                        <input id="usesAVC" name="usesAVC" type="checkbox" ${' checked="checked" ' if candResv.usesAVC else ""} />
                                        ${contextHelp('iWillUseVideoConferencing' )}
                                    </td>
                                </tr>
                                <tr>
                                    <td align="right" class="subFieldWidth" valign="middle">
                                        <span style="color: Red;">I will use video-conf. system</span>&nbsp;&nbsp;
                                    </td>
                                    <td align="left" id="vcSystemList" class="blacktext">
                                        % for vc in candResv.room.getAvailableVC():
                                            <% checked = "" %>
                                            % if vc in candResv.getUseVC():
                                                <% checked = """checked="checked" """ %>
                                            % endif
                                            <% htmlCheckbox = """<br>\n<input id="vc_%s" name="vc_%s" class="videoConferenceOption" type="checkbox" %s /> %s""" %>
                                            ${ htmlCheckbox % (vc[:3], vc[:3], checked, vc) }
                                        % endfor
                                    </td>
                                </tr>
                            % endif
                            % if candResv.room.needsAVCSetup or (rh._isAssistenceEmailSetup and candResv.room.resvNotificationAssistance):
                            <tr>
                                <td align="right" class="subFieldWidth" valign="top">
                                    ${ _("Assistance")}&nbsp;&nbsp;
                                </td>
                                <td>
                                    <table valign='top' cellpadding=0 cellspacing=0>
                                        % if candResv.room.needsAVCSetup:
                                        <tr>
                                            <td align="left" class="blacktext">
                                                <table cellpadding=0 cellspacing=0>
                                                <tr>
                                                    <td style="vertical-align:top;">
                                                        <input id="needsAVCSupport" name="needsAVCSupport" type="checkbox" ${' checked="checked" ' if candResv.needsAVCSupport else ""} />
                                                    </td>
                                                    <td style="width:100%;padding-left: 3px;">
                                                        ${ _("Request assistance for the startup of the videoconference session. This support is usually performed remotely.")}
                                                    </td>
                                                </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        % endif
                                        % if rh._isAssistenceEmailSetup and candResv.room.resvNotificationAssistance:
                                        <tr>
                                            <td align="left" class="blacktext">
                                                <table cellpadding=0 cellspacing=0>
                                                <tr>
                                                    <td style="vertical-align:top;">
                                                        <input id="needsAssistance" name="needsAssistance" type="checkbox" ${' checked="checked" ' if candResv.needsAssistance else ""} />
                                                    </td>
                                                    <td style="width:100%;padding-left: 3px;">
                                                        ${_("Request assistance for the startup of your meeting. A technician will be physically present 10 to 15 minutes before the event to help you start up the room equipment (microphone, projector, etc)")}
                                                    </td>
                                                </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        % endif
                                    </table>
                                </td>
                            </tr>
                            % endif
                        </table>
                    </td>
                </tr>
                <!-- ACTIONS -->
                <tr>
                    <td>
                        <div class="groupTitle bookingTitle"></div>
                    </td>
                </tr>
                <tr>
                    <td>
                        <input type="hidden" name="conf" value="${ conf.getId()  if conf else ''}" />
                        <input type="hidden" name="standalone" value="${ standalone }" />
                        <ul id="button-menu" class="ui-list-menu ui-list-menu-level ui-list-menu-level-0 " style="float:left;">
                          <li class="button" style="margin-left: 10px" onclick="saveBooking()">
                            <a href="#" onClick="return false;">${'Save' if formMode==FormMode.MODIF else bookingMessage}</a>
                          </li>
                          <li style="display: none"></li>
                        </ul>
                        <div style="padding-top: 5px;">
                            <input type="checkbox" name="skipConflicting" id="skipConflicting" ${' checked="checked" ' if skipConflicting else ""} />
                             ${ _("Skip conflicting dates")}
                            ${contextHelp('skipConflictsHelp' )}
                        </div>
                    </td>
                </tr>
            </table>
            </td>
        </tr>
    </table>
    </form>
