<h2 class="page-title">
    ${ _('Room statistics') }
</h2>

<table>
    <tr>
        <td>
            % if room.has_photo:
                <a href="${ room.large_photo_url }" class="js-lightbox">
                    <img border="1px" height="100" src="${ room.small_photo_url }"/>
                </a>
            % endif
        </td>
        <td>
            <table>
                <tr>
                    <td align="right" valign="top">
                        ${ ('Location') }
                    </td>
                    <td align="left" class="blacktext">
                        ${ room.location_name }
                    </td>
                </tr>
                <tr>
                    <td align="right" valign="top">${ _('Name') }</td>
                    <td align="left" class="blacktext">${ room.name }</td>
                </tr>
                <tr>
                    <td align="right" valign="top">${ _('Site') }</td>
                    <td align="left" class="blacktext">${ room.site }</td>
                </tr>
                <tr>
                    <td align="right" valign="top">${ _('Building') }</td>
                    <td align="left" class="blacktext">
                        <a href="https://maps.cern.ch/mapsearch/mapsearch.htm?no=[${ room.building }]" title="Show on map">
                            ${ room.building }
                        </a>
                    </td>
                </tr>
                <tr>
                    <td align="right" valign="top">${ _('Floor') }</td>
                    <td align="left" class="blacktext">${ room.floor }</td>
                </tr>
                <tr>
                    <td align="right" valign="top">${ _('Room') }</td>
                    <td align="left" class="blacktext">${ room.number }</td>
                </tr>
            </table>
        </td>
    </tr>
</table>


<h2 class="group-title">
    ${ _('Key Performance Indicators') }
</h2>

<div class="i-box-group horz">
    <div class="i-box">
        <div class="i-box-header">
            <div class="i-box-title">
                ${ _('Booking stats') }
            </div>
        </div>
        <div class="i-box-content">
            <table class="booking-stats" cellspacing="0">
                <tr>
                    <td></td>
                    <td>${ _('Valid') }</td>
                    <td>${ _('Pending') }</td>
                    <td>${ _('Cancelled') }</td>
                    <td>${ _('Rejected') }</td>
                    <td>${ _('Total') }</td>
                </tr>
                <tr>
                    <td>${ _('Active') }</td>
                    <td class="active-valid">
                        ${ stats['active']['valid'] }
                    </td>
                    <td>${ stats['active']['pending'] }</td>
                    <td>${ stats['active']['cancelled'] }</td>
                    <td>${ stats['active']['rejected'] }</td>
                    <td>
                        ${ stats['active']['valid'] + \
                           stats['active']['cancelled'] + \
                           stats['active']['rejected'] }
                    </td>
                </tr>
                <tr>
                    <td>${ _('Archived') }</td>
                    <td>${ stats['archived']['valid'] }</td>
                    <td>${ stats['archived']['pending'] }</td>
                    <td>${ stats['archived']['cancelled'] }</td>
                    <td>${ stats['archived']['rejected'] }</td>
                    <td>
                        ${ stats['archived']['valid'] + \
                           stats['archived']['cancelled'] + \
                           stats['archived']['rejected'] }
                    </td>
                </tr>
                <tr>
                    <td>${ _('Total') }</td>
                    <td>${ stats['active']['valid'] + stats['archived']['valid'] }</td>
                    <td>${ stats['active']['pending'] + stats['archived']['pending'] }</td>
                    <td>${ stats['active']['cancelled'] + stats['archived']['cancelled'] }</td>
                    <td>${ stats['active']['rejected'] + stats['archived']['rejected'] }</td>
                    <td class="total-bookings">
                        ${ stats['active']['valid'] + stats['archived']['valid'] + \
                           stats['active']['pending'] + stats['archived']['pending'] + \
                           stats['active']['cancelled'] + stats['archived']['cancelled'] + \
                           stats['active']['rejected'] + stats['archived']['rejected'] }
                    </td>
                </tr>
            </table>
        </div>
    </div>
    <div class="i-box occupancy-stats">
        <div class="i-box-header">
            <div class="i-box-header-text">
                <div class="i-box-title">
                    ${ _('Occupancy') }
                </div>
            </div>
            <div class="i-box-buttons toolbar thin">
                <div class="group i-selection">
                    % for key, text in period_options:
                        <% checked = 'checked' if period == key else '' %>
                        <input type="radio" id="${ key }" name="period" value="${ key }" ${ checked }>
                        <label for="${ key }" class="i-button">${ text }</label>
                    % endfor
                </div>
            </div>
        </div>
        <div class="i-box-content">
            <table cellspacing="0">
                <tr>
                    <td class="occupancy-period">
                        ${ _('Average room occupancy in weekdays during working hours') }
                        % if period == 'pastmonth':
                            ${ _('over the past 30 days') }.
                        % elif period == 'thisyear':
                            ${ _('since the beginning of this year') }.
                        % else:
                            ${ _('since the first booking ever registered') }.
                        % endif
                    </td>
                    <td class="occupancy-value">
                        ${ '{0:.02f}'.format(occupancy * 100) }<small>%</small>
                    </td>
                </tr>
            </table>
        </div>
    </div>
</div>

<script>
    $(function(){
        $('input[name=period]').on('change', function(e) {
            var url_template = ${ url_rule_to_js('rooms.roomBooking-roomStats') | n,j };
            location.href = build_url(url_template, {
                roomLocation: ${ room.location_name | n, j},
                roomID: ${ room.id | n, j },
                period: this.value
            });
        });
    });
</script>
