<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <input type="hidden" value="${confId}" id="conf_id">
    <table width="100%">
        <tr>
            <td>
                <table width="100%" align="center">
                    <tr>
                        <td nowrap class="displayField">${ _("Registration opening day")}:</td>
                        <td width="100%" align="left">${ startDate }</td>
                    </tr>
                    <tr>
                        <td nowrap class="displayField">${ _("Registration deadline")}:</td>
                        <td width="100%" align="left">${ endDate }</td>
                    </tr>
                    ${ usersLimit }
                    ${ contactInfo }
                </table>
            </td>
        </tr>
        <tr>
            <td><br></td>
        </tr>
        <tr>
            <td>
                <table width="100%" align="center">
                    <tr>
                        <td><pre>${ announcement }</pre></td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                <table width="100%" align="center" style="padding-top:20px">
                    <tr>
                        <td>${ actions }</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    <br>
</%block>
