<%page args="form=None, reservation=None"/>

% if conflicts:
    <div class="warning-message-box new-booking-message-box">
        <div class="message-text">
            ${ _('Some of your days will not be booked as they overlap with other existing bookings.') }
            <ul>
                % for occurrence, overlap in conflicts.iteritems():
                <li>
                    ${ format_date(occurrence.start, format='full') }:
                    <ul>
                        % for occ in overlap:
                        <li>
                            <small>
                                ${ format_time(occ.start) } -
                                ${ format_time(occ.end) }
                                ${ _('by') }
                                ${ occ.reservation.booked_for_name }
                                (<a href="${ occ.reservation.details_url }">more info</a>)
                            </small>
                        </li>
                        % endfor
                    </ul>
                </li>
                % endfor
            </ul>
        </div>
        <div class="message-box-footer">
            <input type="checkbox" id="conflict-warning" name="conflict-warning" class="js-confirm-warning">
            <label for="conflict-warning">${ _('I understand') }</label>
        </div>
    </div>
% endif

% if pre_conflicts:
    <div class="info-message-box new-booking-message-box">
        <div class="message-text">
            % if form.submit_book:
                <div>
                    ${ _('If you book, overlapping days of the following pre-bookings will automatically be rejected.') }
                </div>
            % elif reservation and reservation.is_confirmed:
                <div>
                    ${ _('If you update this booking, overlapping days of the following pre-bookings will automatically be rejected.') }
                </div>
            % endif
            % if form.submit_prebook:
                <div>
                    ${ _('If you pre-book, some of your days may get rejected as they overlap with other existing pre-bookings.') }
                </div>
            % elif reservation and not reservation.is_confirmed:
                <div>
                    ${ _('If you update this pre-booking, some of your days may get rejected as they overlap with other existing pre-bookings.') }
                </div>
            % endif
            <ul>
                % for occurrence, overlap in pre_conflicts.iteritems():
                <li>
                    ${ format_date(occurrence.start, format='full') }:
                    <ul>
                        % for preocc in overlap:
                        <li>
                            <small>
                                ${ format_time(preocc.start) } -
                                ${ format_time(preocc.end) }
                                ${ _('by') }
                                ${ preocc.reservation.booked_for_name }
                                (<a href="${ preocc.reservation.details_url }">more info</a>)
                            </small>
                        </li>
                        % endfor
                    </ul>
                </li>
                % endfor
            </ul>
        </div>
        <div class="message-box-footer">
            <input type="checkbox" id="preconflict-warning" name="preconflict-warning" class="js-confirm-warning">
            <label for="preconflict-warning">${ _('I understand') }</label>
        </div>
    </div>
% endif

<div class="error-message-box js-booking-creation-error-box" style="display: none;">
    <div class="message-text">
        <p>${ _("Your reservation could not be modified:") if reservation else _("Your reservation could not be created:") }</p>
        <ul>
            <li class="js-booking-creation-error-message"></li>
        </ul>
    </div>
</div>
