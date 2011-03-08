<%page args="DAY_WIDTH_PX=None, START_H=None, dayD=None"/>

<tr style="height: 40px;">
    <td width="120px">
        % if dayD: 
            <strong>${ formatDate(dayD) }</strong>
        % endif
        % if not dayD: 
             ${ _("Date")}
        % endif
    </td>
    <td style="width: ${ DAY_WIDTH_PX }px; ">
        <div style="height: 12px; position: relative;">
            % for h in xrange( START_H, 25, 2 ): 
                <div id="barDivH_Hours" style="position: absolute; height: 10px; left: ${ int( 1.0 * (h-START_H) / 24 * DAY_WIDTH_PX ) }px; font-size: 10px; " >
                    ${ "%.2d" % h }<span style="font-size: 8px">:00</span>
                </div>
            % endfor
        </div>
    </td>
</tr>
