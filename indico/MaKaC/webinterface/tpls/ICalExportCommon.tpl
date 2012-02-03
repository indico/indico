
<div id="exportICalDialogs" style="display:none">
    <div id="agreementApiKey">
        <div id="agreementApiKeyText" class="agreement">
            ${_("""You need to create an HTTP API key in order to retrieve the information from the HTTP API. You can do so by accepting the agreement below or from <a href="%s" target="_blank">My Profile</a>, where you can also manage it.""") % (urlHandlers.UHUserAPI.getURL(self_._aw.getUser()))}
        </div>
        <input type="checkbox" id="agreeCheckBoxKey"> ${("I read the agreement.")}
        <input id="agreementButtonKey" type="submit" value="Agree" disabled="disabled"/>
        <div style="display:inline;" id="progressPersistentKey"></div>
    </div>
    <div id="agreementPersistentSignatures">
        <div id="agreementPersistentSignaturesText" class="agreement">
            <div>${apiPersistentEnableAgreement}</div>
        </div>
        <input type="checkbox" id="agreeCheckBoxPersistent"> ${("I read the agreement.")}
        <input id="agreementButtonPersistent" type="submit" value="Agree" disabled="disabled"/>
        <div style="display:inline;" id="progressPersistentSignatures"></div>
    </div>
    <input id="publicLink" type="text" class="apiURL" readonly/>
    <input id="authLink" type="text" class="apiURL" readonly/>
</div>

<div id="publicLinkWrapper"  class="iCalExportSection" style="display:none">
    <div class="exportIcalHeader">${_('Link for public information only:')}</div>
</div>

<div id="authLinkWrapper" class="iCalExportSection" style="display:none">
    <div class="exportIcalHeader">${_('Link for all public and protected information:')}</div>
</div>




