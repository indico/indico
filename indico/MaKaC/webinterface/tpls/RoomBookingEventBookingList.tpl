<table width="80%">
    <tr>
        <td>
            <table>
                <tr>
                    <td class="groupTitle">
                        ${ _("Existing bookings")}
                    </td>
                </tr>
                <tr>
                    <td style="white-space: nowrap;">
                        <table class="resvTable">
                            <tr>
                                <td class="dataCaptionFormat">${ _("Photo")}</td>
                                <td class="dataCaptionFormat">${ _("Room")}</td>
                                <td class="dataCaptionFormat">${ _("Reason")}<br>${ _("For whom")}</td>
                                <td class="dataCaptionFormat">${ _("Date")}</td>
                                <td class="dataCaptionFormat">${ _("Hours")}</td>
                                <td class="dataCaptionFormat">${ _("Actions")}</td>
                            </tr>
                            <tr>
                                <td class="titleCellTD" colspan="5" style="height: 0">&nbsp;</td>
                            </tr>

                            % for reservation in reservations:
                                <%
                                    details_url = url_for('event_mgmt.rooms_booking_details', event, reservation)
                                    onclick = 'onclick="window.location=\'{}\'"'.format(details_url)
                                    style = 'text-decoration: line-through;' if reservation.is_rejected or reservation.is_cancelled else ''
                                %>

                                <tr style="height: 60px;">
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer;">
                                        % if reservation.room.has_photo:
                                            <img src="${ reservation.room.small_photo_url }">
                                        % else:
                                            &nbsp;
                                        % endif
                                    </td>
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer; vertical-align: top; white-space: nowrap; ${ style }">
                                        ${ reservation.room.full_name }
                                    </td>
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer; vertical-align: top; ${ style }">
                                        ${ reservation.booking_reason }<br>
                                        ${ reservation.booked_for_name }
                                    </td>
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer; vertical-align: top; ${ style }">
                                        ${ formatDate(reservation.start_dt) }
                                        % if reservation.is_repeating:
                                            (recurring)
                                        % endif
                                    </td>
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer; vertical-align: top; white-space: nowrap; ${ style }">
                                        ${ verbose_t(reservation.start_dt) }
                                        -
                                        ${ verbose_t(reservation.end_dt) }
                                    </td>
                                    <td ${onclick} style="padding: 0 10px 6px 0; cursor: pointer; vertical-align: top;">
                                        <a href="${ details_url }">${ _('Details') }</a>
                                    </td>
                                </tr>
                            % endfor
                            <tr>
                                <td class="titleCellTD" colspan="5" style="height: 0;">&nbsp;</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
