type("ExportIcalInterface", [], {
    _getExportURLs: function(progressTarget) {
        var self = this;
        $.ajax({
            url: self.getURLsMethod,
            type: 'POST',
            data: JSON.stringify(self.getURLsParams),
            dataType: 'json',
            contentType: 'application/json',
            error: handleAjaxError,
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                self.setURLsFunction(data.urls);
                switch (self.apiMode) {
                    case 0:
                        if (self.apiActive) {
                            self._postAcceptAgreements('#agreementApiKey' + self.id);
                        }
                        break;
                    case 1:
                        if (self.apiActive) {
                            $('#publicLinkWrapper' + self.id).append($("#publicLink" + self.id)).show();
                            self._postAcceptAgreements('#agreementApiKey' + self.id);
                        }
                        break;
                    case 2:
                        if (self.apiActive) {
                            $('#agreementApiKey' + self.id).hide();
                            if (self.persistentUserEnabled && self.persistentAllowed) {
                                self._postAcceptAgreements('#agreementPersistentSignatures' + self.id);
                            }
                        }
                        break;
                    case 3:
                        if (self.apiActive) {
                            $('#publicLinkWrapper' + self.id).append($("#publicLink" + self.id)).show();
                            if (self.persistentUserEnabled && self.persistentAllowed) {
                                self._postAcceptAgreements('#agreementPersistentSignatures' + self.id);
                            } else {
                                $('#extraInformation' + self.id).insertAfter('#publicLinkWrapper' + self.id);
                            }
                            $('#agreementApiKey' + self.id).hide();
                        }
                        break;
                    case 4:
                        if (self.apiActive) {
                            $('#agreementApiKey' + self.id).hide();
                            if (self.persistentUserEnabled && self.persistentAllowed) {
                                $('#publicLinkWrapper' + self.id).append($("#publicLink" + self.id)).show();
                                self._postAcceptAgreements('#agreementPersistentSignatures' + self.id);
                            }
                        }
                        break;
                }
            }
        });
    },

    _showPrivatePanel: function(question){
        var self = this;
        if(self.persistentAllowed){
            if(self.persistentUserEnabled){
                self._showAuthLink();
            }else{
                question = question || $T("Would you like to export private information to your calendar?");
                var privateInfo = $("<span class='fakeLink'>"+question+"</span>");

                $('#authLinkWrapper'+self.id).append(privateInfo).show();

                privateInfo.click(function(){
                    privateInfo.hide();
                    $('#exportIcalHeader'+self.id).show();
                    $('#authLinkWrapper'+self.id).append($("#agreementPersistentSignatures"+self.id)).show();
                });
            }
            $('#iCalSeparator'+self.id).show();
        }
    },

    _postAcceptAgreements: function(targetAgreement){
        $('#authLinkWrapper'+this.id).append($("#authLink"+this.id)).show();
        $('#extraInformation'+this.id).insertAfter('#authLinkWrapper'+this.id);
        $(targetAgreement).hide();
    },

    _showAuthLink: function(){
        $('#exportIcalHeader'+this.id).show();
        $('#authLinkWrapper'+this.id).append($("#authLink"+this.id)).show();
        $('#extraInformation'+this.id).insertAfter('#authLinkWrapper'+this.id);
    },

    _showAgreement: function(agreementTarget){
        $('#extraInformation').insertAfter('#publicLinkWrapper'+this.id);
        $('#authLinkWrapper'+this.id).append($(agreementTarget)).show();
    },

    getRequestURLs: function(){
        return this.requestURLs;
    },

    createKey: function(enablePersistent, progressTarget){
        var self = this;
        $(progressTarget).html($(progressIndicator(true, false).dom));
        $.ajax({
            url: Indico.Urls.APIKeyCreate,
            method: 'POST',
            dataType: 'json',
            data: {
                quiet: '1',
                persistent: enablePersistent ? '1': '0'
            },
            error: function(xhr) {
                handleAjaxError(xhr);
                $(progressTarget).html('');
            },
            success: function(data) {
                self.apiActive = true;
                self.persistentUserEnabled = data.is_persistent_allowed;
                self._getExportURLs(progressTarget);
            }
        });
    },

    enablePersistentSignatures: function() {
        var self = this;
        if (self.apiActive) {
            $.ajax({
                url: Indico.Urls.APIKeyTogglePersistent,
                method: 'POST',
                dataType: 'json',
                data: {
                    enabled: '1',
                    quiet: '1'
                },
                error: function(xhr) {
                    handleAjaxError(xhr);
                    $('#progressPersistentSignatures').html('');
                },
                success: function(data) {
                    self.persistentUserEnabled = data.enabled;
                    self._getExportURLs('progressPersistentSignatures');
                }
            });
        }

        else{
            self.createKey(true, '#progressPersistentSignatures');
        }
    },

    showPopup: function(){
        $('#icalExportPopup'+this.id).show();
    },

    showContent: function(){
        var self = this;
        self.setURLsFunction(self.requestURLs);
        switch(self.apiMode){
        case 0://Public:nothing; Private:API_KEY
            $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
            if(self.userLogged){
                if (self.apiActive){
                    self._showAuthLink();
                } else{
                    $('#exportIcalHeader'+self.id).show();
                    self._showAgreement('#agreementApiKey'+self.id);
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 1://Public:API_KEY; Private:API_KEY
            if(self.userLogged){
                if (self.apiActive){
                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                    self._showAuthLink();
                } else{
                    $('#exportIcalHeader'+self.id).show();
                    $('#authLinkWrapper'+self.id).append($("#agreementApiKey"+self.id)).show();
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 2://Public:nothing; Private:SIGNED
            $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
            if(self.userLogged){
                self._showPrivatePanel();
            }
            else {
                $('#extraInformation'+self.id).insertAfter('#publicLinkWrapper'+self.id);
            }
            $('#iCalSeparator'+self.id).show();
            break;
        case 3://Public:API_KEY; Private:SIGNED
            if(self.userLogged){
                if(self.apiActive){
                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                } else{
                    $('#publicLinkWrapper'+self.id).append($("#agreementApiKey"+self.id)).show();
                }
                self._showPrivatePanel();
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 4://ALL_SIGNED
            if(self.userLogged){
                if(self.persistentAllowed){
                    if(self.persistentUserEnabled){
                        $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                    }
                    self._showPrivatePanel($T("Would you like to create a persistent URL for use with your calendaring application?"));
                }
            }
            break;
        };
    }

}, function(apiMode, persistentUserEnabled, persistentAllowed, apiActive, userLogged, setURLsFunction, getURLsMethod,
            getURLsParams, requestURLs, id, userId) {
    this.apiMode = any(apiMode, 0);
    this.persistentUserEnabled = any(persistentUserEnabled, false);
    this.persistentAllowed = any(persistentAllowed, false);
    this.apiActive = any(apiActive, false);
    this.userLogged = any(userLogged, false);
    this.setURLsFunction = setURLsFunction;
    this.getURLsMethod = any(getURLsMethod, "");
    this.getURLsParams = any(getURLsParams, {});
    this.requestURLs = any(requestURLs, {});
    this.id = any(id, "");
    this.userId = any(userId, "");

    this.showContent();
});


var exportPopups = {};

$(document).ready(function() {
    $(".js-export-ical").on('menu_select', function() {
        var $button = $(this);

        if ($button.hasClass('open')) {
            return;
        } else {
            $button.addClass('open');

            $("<a>").qtip({
                style: {
                    width: '350px',
                    classes: 'qtip-rounded qtip-shadow qtip-popup',
                    tip: {
                        corner: true,
                        width: 20,
                        height: 15
                    }
                },
                position: {
                    my: 'top center',
                    at: 'bottom center',
                    target: $button
                },
                content: function(api) {
                    return $('#icalExportPopup' + $button.data("id"));
                },
                show: {
                    ready: true,
                    effect: function() {
                        $(this).fadeIn(300);
                    }
                },
                events: {
                    hide: function() {
                        $(this).fadeOut(300);
                        $button.removeClass('open');
                    }
                },
                hide: {
                    event: 'unfocus',
                    fixed: true,
                    target: $button
                }
            });
        }

        return true;
    });

    $('body').delegate('.apiURL','click',function(e){
        $(this).select();
    }).delegate('.agreementButtonPersistent','click',function(e){
        var id = $(this).data('id');
        $('#progressPersistentSignatures'+id).html($(progressIndicator(true, false).dom));
        exportPopups[id].enablePersistentSignatures();
    }).delegate('.agreementButtonKey','click',function(e){
        var id = $(this).data('id');
        exportPopups[id].createKey(false, '#progressPersistentKey'+id);
    }).delegate('.agreeCheckBoxKey','click',function(e){
        var id = $(this).data('id');
        $('#agreementButtonKey' + id).prop('disabled', !this.checked);
    }).delegate('.agreeCheckBoxPersistent','click',function(e){
        var id = $(this).data('id');
        $('#agreementButtonPersistent'+id).prop('disabled', !this.checked);
        $('#agreeCheckBoxKey'+id).prop('checked', this.checked).prop('disabled', this.checked);
        if(this.checked){
            $('#agreementButtonKey'+id).prop('disabled', true);
        }
    });
});
