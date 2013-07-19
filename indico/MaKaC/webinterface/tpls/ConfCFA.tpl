<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <table width="90%" align="center">
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td>
                <table>
                    <tr>
                        <td nowrap class="displayField"><b> ${ _("Abstract submission opening day")}:</b></td>
                        <td width="100%" align="left">${ startDate }</td>
                    </tr>
                    <tr>
                        <td nowrap class="displayField"><b> ${ _("Abstract submission deadline")}:</b></td>
                        <td width="100%" align="left">${ endDate }</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td><br></tr>
        </tr>
        <tr>
            <td>
                <table>
                    <tr>
                        <td>${ announcement }</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                <table style="padding-top:20px">
                    <tr>
                        <td>${ actions }</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br>
</%block>


