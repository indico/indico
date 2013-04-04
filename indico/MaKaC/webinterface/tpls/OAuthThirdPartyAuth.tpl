
<div style="margin: 0px auto; text-align:center">
    <div class="confirmation-dialog">
        <div class="pageHeaderMainPage" style="margin-bottom: 20px; padding: 0px 5px 5px 0px;">
            <div style="text-align: left">
                <a href="${ Config.getInstance().getBaseURL() }/index.py">
                    <img alt="logo" class="headerLogo" src="${ Config.getInstance().getSystemIconURL("logoIndico") }" />
                </a>
            </div>
            <div style="text-align: right; font-weight: bold; color: #555;">${user.getStraightFullName()}</div>
        </div>
        <div class="body" style="float:none; text-align:justify">
            <div><b>${third_party_app}</b> ${ _(" needs to access to the events you have access permission. The access will be read-only and no modifications will be performed to these events. ")}</div>
            <div>${ _("Do you grant access to")} <b>${ third_party_app }</b>?</div>
        </div>
        <div class="i-buttons">
            <a href="${refuseURL}" class="i-button right" >${_("Refuse")}</a>
            <a href="${allowURL}" class="i-button right highlight" >${_("Allow")}</a>
        </div>
    </div>
</div>
