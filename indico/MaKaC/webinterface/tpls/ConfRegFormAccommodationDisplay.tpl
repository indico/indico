<table width="100%" align="left" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
    <tr>
        <td nowrap class="groupTitle" style="background:#E5E5E5; color:gray"><b>${ title }</b></td>
    </tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td style="padding-left:10px">
            <table width="100%">
                <tr>
                    <td align="left"><pre style="white-space:normal">${ description }</pre></td>
                </tr>
                <tr>
                    <td align="left">&nbsp;</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td style="padding-left:10px">
            <table align="left">
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font>${ _("Arrival date")}:</td>
                    <td align="left">&nbsp; ${ arrivalDate }</td>
                </tr>
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font>${ _("Departure date")}:</td>
                    <td align="left">&nbsp;${ departureDate }</td>
                </tr>
            </table>
        </td>
    </tr>
    <tr><td>&nbsp;</td></tr>
% if accommodationTypes != "":
    <tr>
        <td style="padding-left:10px">
            <table align="left">
                <tr>
                    <td align="left">&nbsp;<font color="red">* </font><span id="accommodationTypeLabel" style="font-weight: bold;">${ _("Select your accommodation")}:</span></td>
                </tr>
                ${ accommodationTypes }
            </table>
        </td>
    </tr>
% endif
</table>
