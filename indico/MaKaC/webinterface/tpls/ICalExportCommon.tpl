<%page args="id=None"/>
<div id="exportICalDialogs" style="display:none">
    <div id="agreementApiKey${id}">
        <div id="agreementApiKeyText" class="agreement">
            <div>${apiKeyUserAgreement}</div>
        </div>
        <input type="checkbox" id="agreeCheckBoxKey${id}" data-id="${id}" class="agreeCheckBoxKey"> ${_("I have read and understood the above.")}<br/>
        <input id="agreementButtonKey${id}" data-id="${id}" type="submit" value="${_('Accept & Create')}" disabled="disabled" class="agreementButtonKey"/>
        <div style="display:inline;" id="progressPersistentKey${id}" data-id="${id}"></div>
    </div>
    <div id="agreementPersistentSignatures${id}">
        <div id="agreementPersistentSignaturesText" class="agreement">
            <div>${apiPersistentUserAgreement}</div>
        </div>
        <input type="checkbox" id="agreeCheckBoxPersistent${id}" data-id="${id}" class="agreeCheckBoxPersistent"> ${_("I have read and understood the above.")}<br/>
        <input id="agreementButtonPersistent${id}" data-id="${id}" type="submit" value="${_('Accept & Create')}" disabled="disabled" class="agreementButtonPersistent"/>
        <div style="display:inline;" id="progressPersistentSignatures${id}" data-id="${id}"></div>
    </div>
    <input id="publicLink${id}" type="text" class="apiURL" readonly/>
    <input id="authLink${id}" type="text" class="apiURL" readonly/>
</div>

<div id="publicLinkWrapper${id}"  class="iCalExportSection" style="display:none">
    <div class="exportIcalHeader">${_('Permanent link for public information only:')}</div>
</div>

<div id="authLinkWrapper${id}" class="iCalExportSection" style="display:none">
    <div id="exportIcalHeader${id}" class="exportIcalHeader" style="display:none">${_('Permanent link for all public and protected information:')}</div>
</div>



