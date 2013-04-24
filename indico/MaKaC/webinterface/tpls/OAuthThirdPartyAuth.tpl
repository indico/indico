<div class="pageHeaderMainPage" style="text-align: center; margin-bottom: 20px;">
    <table style="margin: 0px auto; width: 630px;">
        <tbody>
            <tr>
                <td>
                    <a href="${Config.getInstance().getBaseURL()}">
                        <img alt="logo" style="float:left" class="headerLogo" src="${ Config.getInstance().getSystemIconURL("logoIndico") }" />
                    </a>
                </td>
                <td style="vertical-align: bottom">
                    <div style="text-align: right; font-weight: bold; color: #555; margin-bottom: 10px">${user.getStraightFullName()}</div>
                </td>
            </tr>
        </tbody>
    </table>
</div>
<div style="margin: 0px auto; text-align:center">
    <div class="confirmation-dialog">

        <div class="body" style="float:none; text-align:justify">
            <div><b>${third_party_app}</b> ${ _(" is requesting access to the events you have access permission. The access will be read-only and no modifications will be performed on these events.")}</div>
            <div>${ _("Do you grant access to")} <b>${ third_party_app }</b>?</div>
        </div>
        <div class="i-buttons">
            <a href=${quoteattr(refuseURL)} class="i-button right" >${_("Refuse")}</a>
            <a href=${quoteattr(allowURL)} class="i-button right highlight" >${_("Allow")}</a>
        </div>
    </div>
</div>
