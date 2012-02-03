<%page args="id=None"/>
<div id="exportICalDialogs" style="display:none">
    <div id="agreementApiKey${id}">
        <div id="agreementApiKeyText" class="agreement">
            ${_("""You need to create an HTTP API key in order to retrieve the information from the HTTP API. You can do so by accepting the agreement below or from <a href="%s" target="_blank">My Profile</a>, where you can also manage it.""") % (urlHandlers.UHUserAPI.getURL(currentUser))}
        </div>
        <input type="checkbox" id="agreeCheckBoxKey${id}" data-id="${id}" class="agreeCheckBoxKey"> ${("I read the agreement.")}
        <input id="agreementButtonKey${id}" data-id="${id}" type="submit" value="Agree" disabled="disabled" class="agreementButtonKey"/>
        <div style="display:inline;" id="progressPersistentKey${id}" data-id="${id}"></div>
    </div>
    <div id="agreementPersistentSignatures${id}">
        <div id="agreementPersistentSignaturesText" class="agreement">
            <div>${apiPersistentEnableAgreement}</div>
        </div>
        <input type="checkbox" id="agreeCheckBoxPersistent${id}" data-id="${id}" class="agreeCheckBoxPersistent"> ${("I read the agreement.")}
        <input id="agreementButtonPersistent${id}" data-id="${id}" type="submit" value="Agree" disabled="disabled" class="agreementButtonPersistent"/>
        <div style="display:inline;" id="progressPersistentSignatures${id}" data-id="${id}"></div>
    </div>
    <input id="publicLink${id}" type="text" class="apiURL" readonly/>
    <input id="authLink${id}" type="text" class="apiURL" readonly/>
</div>

<div id="publicLinkWrapper${id}"  class="iCalExportSection" style="display:none">
    <div class="exportIcalHeader">${_('Link for public information only:')}</div>
</div>

<div id="authLinkWrapper${id}" class="iCalExportSection" style="display:none">
    <div class="exportIcalHeader">${_('Link for all public and protected information:')}</div>
</div>




