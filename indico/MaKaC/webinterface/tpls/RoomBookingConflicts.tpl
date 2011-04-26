<table width="100%">
    <tr>
        <td width="12%" class="dataCaptionFormat"> ${ _("Conflict Dates")}</td>
        <td width="18%" class="dataCaptionFormat"> ${ _("Conflict Hours")}</td>
        <td width="60%" class="dataCaptionFormat"> ${ _("Already booked for")}</td>
    </tr>

<!-- Render each conflict... -->
<% c = 0; ks = bars.keys(); ks.sort()  %>
% for dt in ks:
    % for bar in bars[dt]:
        % if bar.type == Bar.CONFLICT:
            <tr>
                <td>${ formatDate(bar.startDT.date()) }
                <td>${ bar.startDT.time() } -- ${ bar.endDT.time() }</td>
                <td>${ bar.forReservation.bookedForName }</td>
            </tr>

            <% c += 1 %>
            % if c > 4:
                <% break %>
            % endif

        % endif
    % endfor
% endfor

</table>
