<table class="regFormSectionTable" width="100%" align="left" cellspacing="0">
    <tr>
        <td nowrap class="regFormSectionTitle">${ title }</td>
    </tr>
    % if description:
    <tr>
        <td style="padding: 10px 0 0 15px;">
            <table width="100%">
                <tr>
                    <td align="left"><pre>${ description }</pre></td>
                </tr>
            </table>
        </td>
    </tr>
    % endif
    <tr>
        <td style="padding: 10px 0 0 15px;" align="left" valign="top">
            <table align="left" valign="top">
                ${ fields }
            </table>
        </td>
    </tr>
</table>
