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

        var isValid = true;
        isValid = validate_period(bookingForm[0], true, ${allowPast}) && isValid;
        isValid = required_fields(['bookedForName', 'contactEmail', 'reason']) && isValid;

        if (!Util.Validation.isEmailList($('#contactEmail').val())) {
            isValid = false;
            $('#contactEmail').addClass('invalid');
        }

        // Holidays warning
        if (isValid && !onSubmit) {
            var lastDateInfo = bookingForm.data('lastDateInfo');
            var dateInfo = $('#sDay, #sMonth, #sYear, #eDay, #eMonth, #eYear').serialize();
            if (dateInfo != lastDateInfo) {
                bookingForm.data('lastDateInfo', dateInfo);
                var holidaysWarning = indicoSource('roomBooking.getDateWarning', bookingForm.serializeObject());

                holidaysWarning.state.observe(function(state) {
                    if (state == SourceState.Loaded) {
                        $E('holidays-warning').set(holidaysWarning.get());
                    }
                });
            }
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
                                     true, true,
                                     function(users) {
                                         $E('bookedForName').set(users[0].name);
                                         $E('bookedForId').set(users[0].id);
                                         $E('contactEmail').set(users[0].email);
                                     });

        popup.execute();
    }


    $(window).load(function() {
        % if candResv.room.needsAVCSetup:
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

        if (forms_are_valid()) {
            set_repeatition_comment();
        }

        $('#bookingForm').delegate(':input', 'keyup change', function() {
            forms_are_valid();
        }).submit(function(e) {
            if (!forms_are_valid(true)) {
                e.preventDefault();
                alert(${_("'There are errors in the form. Please correct the fields with red background.'")});
            };
        }).keydown(function(e) {
            if(e.which == 13 && !$(e.target).is('textarea, :submit')) {
                e.preventDefault();
                $('#saveBooking').click();
            }
        });

        $('#saveBooking').click(function(e) {
            $('#bookingForm').attr('action', '${saveBookingUH.getURL(conf)}');
        });
        $('#checkBooking').click(function(e) {
            $('#bookingForm').attr('action', '${bookingFormURL}#conflicts');
            if (!validate_period($('#bookingForm')[0], true, ${ allowPast })) {
                alert(${_("'There are errors in the form. Please correct fields with red background.'")});
                e.preventDefault();
            }
        });

        % if candResv.room.needsAVCSetup:
            alert("The conference room you have chosen is equipped\nfor video-conferencing and video-projection.\nIf you need this equipment, DO NOT FORGET to select it.\nIf you don't need any of this equipment please choose\nanother room, if a suitable one is free on a suitable\nlocation for your meeting.\n\n\n                    Thank you for your understanding.")
        % endif
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

    <form id="bookingForm" action="${bookingFormURL}#conflicts" method="post">
    <input type="hidden" id="afterCalPreview" name="afterCalPreview" value="True" />
    <table cellpadding="0" cellspacing="0" border="0" width="80%">
        % if standalone:
            <tr>
            <td class="intermediateleftvtab" style="border-left: 2px solid #777777; border-right: 2px solid #777777; font-size: xx-small;" width="100%">&nbsp;</td> <!-- lastvtabtitle -->
            </tr>
        % endif
        <tr>
            <td class="bottomvtab" width="100%">
                <table width="100%" cellpadding="0" cellspacing="0" class="htab" border="0">
                    <tr>
                        <td class="maincell">
                            <span class="formTitle" style="border-bottom-width: 0px">
                            <input type="hidden" name="roomID" id="roomID" value="${candResv.room.id}" />
                            <input type="hidden" name="roomLocation" id="roomLocation" value="${candResv.room.locationName}" />
                            % if formMode == FormMode.NEW:
                                 ${ _("New")}&nbsp;${bookingMessage}ing
                            % endif
                            % if formMode == FormMode.MODIF:
                                 ${ _("Modify")}&nbsp;${bookingMessage}ing
                                <input type="hidden" name="resvID" id="resvID" value="${candResv.id}" />
                            % endif
                            </span><br />
                            % if showErrors:
                                <br /><a href="#conflicts" style="color: Red; margin-left: 6px;"> ${ _("Saving failed. Please review details below.")}</a><br /><br />
                            % endif
                            <br />
                            <table width="100%" align="left" border="0">
                              <%include file="RoomBookingRoomMiniDetails.tpl" args="room = candResv.room "/>
                              <tr><td>&nbsp;</td></tr>
                              <!-- WHEN -->
                              <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("When")}</span></td>
                                <td>
                                    <table width="100%">
                                        <%include file="RoomBookingPeriodForm.tpl" args="repeatability = candResv.repeatability, form = 0, unavailableDates = candResv.room.getNonBookableDates() "/>
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- BOOKED FOR -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Booked for")}</span></td>
                                <td>
                                    <table width="100%">
                                        % if rh._requireRealUsers:
                                            <tr>
                                                <td class="subFieldWidth" align="right" valign="top"><small> ${ _("User")}&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input type="hidden" id="bookedForId" name="bookedForId" value="${ candResv.bookedForId or '' }" />
                                                    <input type="text" id="bookedForName" name="bookedForName" style="width: 240px;" value="${ candResv.bookedForUser.getFullName() if candResv.bookedForId else candResv.bookedForName }" onclick="searchForUsers();" readonly="readonly" />
                                                    <input type="button" value="Search" onclick="searchForUsers();" />
                                                    ${ inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) }
                                                </td>
                                            </tr>
                                        % elif:
                                            <tr>
                                                <td class="subFieldWidth" align="right" valign="top"><small> ${ _("Name")}&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input type="text" id="bookedForName" name="bookedForName" style="width: 240px;" value="${ verbose( candResv.bookedForName ) }" />
                                                    ${ inlineContextHelp( _("<b>Required.</b> For whom the booking is made.") ) }
                                                </td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td class="subFieldWidth" align="right" valign="top"><small> ${ _("E-mail")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="text" id="contactEmail" name="contactEmail" style="width: 240px;" value="${ verbose( candResv.contactEmail )}" />
                                                ${inlineContextHelp('<b>Required.</b> Contact email. You can specify more than one email address by separating them with commas, semicolons or whitespaces.' )}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" class="subFieldWidth" valign="top"><small> ${ _("Telephone")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <input type="text" id="contactPhone" name="contactPhone" style="width: 240px;" value="${ verbose( candResv.contactPhone ) }" />
                                                ${inlineContextHelp('Contact telephone.' )}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td align="right" class="subFieldWidth" valign="top"><small> ${ _("Reason")}&nbsp;&nbsp;</small></td>
                                            <td align="left" class="blacktext">
                                                <textarea rows="3" cols="50" id="reason" name="reason" >${ verbose( candResv.reason ) }</textarea>
                                                ${inlineContextHelp(_("<b>Required.</b> The justification for booking. Why do you need this room?"))}
                                            </td>
                                        </tr>
                                        % if candResv.room.needsAVCSetup:
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="top"><small><span style="color: Red;">${ _("I will use video-conf. equipment (please check only what you need)")}</span>&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input id="usesAVC" name="usesAVC" type="checkbox" ${' checked="checked" ' if candResv.usesAVC else ""} />
                                                    ${contextHelp('iWillUseVideoConferencing' )}


                                                </td>
                                            </tr>
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="middle"><small><span style="color: Red;">I will use video-conf. system</span>&nbsp;&nbsp;</small></td>
                                                <td align="left" id="vcSystemList" class="blacktext">
                                                    % for vc in candResv.room.getAvailableVC():
                                                        <% checked = "" %>
                                                        % if vc in candResv.getUseVC():
                                                            <% checked = """checked="checked" """ %>
                                                        % endif
                                                        <% htmlCheckbox = """<br>\n<input id="vc_%s" name="vc_%s" class="videoConferenceOption" type="checkbox" %s /> %s""" %>
                                                        ${ htmlCheckbox % (vc[:3], vc[:3], checked, vc) }
                                                    % endfor
                                                    <br><br>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td align="right" class="subFieldWidth" valign="top"><small><span style="color: Red;"> ${ _("I need assistance")}</span>&nbsp;&nbsp;</small></td>
                                                <td align="left" class="blacktext">
                                                    <input id="needsAVCSupport" name="needsAVCSupport" type="checkbox" ${' checked="checked" ' if candResv.needsAVCSupport else ""} />
                                                    ${contextHelp('iNeedAVCSupport' )}
                                                </td>
                                            </tr>
                                        % endif
                                    </table>
                                </td>
                            </tr>
                            <tr><td>&nbsp;</td></tr>
                            <!-- ACTIONS -->
                            <tr>
                                <td class="titleUpCellTD"><span class="titleCellFormat"> ${ _("Actions")}</span></td>
                                <td>
                                       <input type="hidden" name="conf" value="${ conf.getId()  if conf else ""}" />
                                    <input type="hidden" name="standalone" value="${ standalone }" />
                                       <input type="submit" id="checkBooking" class="btn" value="${ _("Re-check for conflicts")}" />
                                       <input type="submit" id="saveBooking" class="btn"  ${' value="Save" ' if formMode==FormMode.MODIF else ""} value="${ bookingMessage }" />
                                    (
                                    <input type="checkbox" name="skipConflicting" id="skipConflicting" ${' checked="checked" ' if skipConflicting else ""} />
                                     ${ _("skip conflicting dates")}
                                    ${contextHelp('skipConflictsHelp' )}
                                    )
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <a name="conflicts"></a>
                                    ${ roomBookingRoomCalendar }
                                </td>
                            </tr>
                        </table>
                        </td>
                    </tr>
                </table>

            </td>
        </tr>
    </table>
    </form>
    <br />