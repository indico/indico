type("ExportIcalInterface", [], {
    _getExportURLs: function(progressTarget) {
        var self = this;
        indicoRequest(self.getURLsMethod, self.getURLsParams,
                function(result, error) {
                    $(progressTarget).html('');
                    if (error){
                        IndicoUI.Dialogs.Util.error(error);
                    }
                    else{
                        self.requestURLs = result;
                        self.setURLsFunction(self.requestURLs);
                        switch(self.apiMode){

                            case 0:
                                if(self.apiActive){
                                    self._postAcceptAgreements('#agreementApiKey');
                                }
                                break;
                            case 1:
                                if(self.apiActive){
                                    $('#publicLinkWrapper').append($("#publicLink")).show();
                                    self._postAcceptAgreements('#agreementApiKey');

                                }
                                break;

                            case 2:
                                if(self.apiActive){
                                    $('#agreementApiKey').hide();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        self._postAcceptAgreements('#agreementPersistentSignatures');
                                    }
                                }
                                break;

                            case 3:
                                if(self.apiActive){
                                    $('#publicLinkWrapper').append($("#publicLink")).show();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        self._postAcceptAgreements('#agreementPersistentSignatures');
                                    }
                                    else {
                                        $('#extraInformation').insertAfter('#publicLinkWrapper');
                                    }
                                    $('#agreementApiKey').hide();
                                }

                                break;

                            case 4:
                                if(self.apiActive){
                                    $('#agreementApiKey').hide();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        $('#publicLinkWrapper').append($("#publicLink")).show();
                                        self._postAcceptAgreements('#agreementPersistentSignatures');
                                    }
                                }
                                break;
                    };
                    }
                });
    },

    _checkPersistentEnabled: function(publicLink){
        var self = this;
        if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed ){
            if(publicLink) $('#publicLinkWrapper').append($("#publicLink")).show();
            self._showAuthLink();
        }else{
            $('#authLinkWrapper').append($("#agreementPersistentSignatures"));
        }
    },

    _postAcceptAgreements: function(targetAgreement){
        $('#authLinkWrapper').append($("#authLink"));
        $('#extraInformation').insertAfter('#authLinkWrapper');
        $(targetAgreement).hide();
    },

    _showAuthLink: function(){
        $('#authLinkWrapper').append($("#authLink"));
        $('#extraInformation').insertAfter('#authLinkWrapper');
    },

    _showAgreement: function(agreementTarget){
        $('#extraInformation').insertAfter('#publicLinkWrapper');
        $('#authLinkWrapper').append($(agreementTarget));
    },

    getAgreementMethod: function(){
        return this.agreementMethod;
    },

    getRequestURLs: function(){
        return this.requestURLs;
    },

    createKey: function(enablePersistent, progressTarget){
        var self = this;
        $(progressTarget).html($(progressIndicator(true, false).dom));
        indicoRequest('user.createKeyAndEnablePersistent', {enablePersistent: enablePersistent},
                function(result, error) {
                    if (error){
                        $(progressTarget).html('');
                        IndicoUI.Dialogs.Util.error(error);
                    }
                    else{
                        self.apiActive = true;
                        self.persistentUserEnabled = enablePersistent;
                        exportIcal._getExportURLs(progressTarget);
                    }
                });
    },

    enablePersistentSignatures: function() {
        var self = this;
        if(self.apiActive){
            indicoRequest('user.togglePersistentSignatures', {},
                    function(result, error) {
                        if (error){
                            $('#progressPersistentSignatures').html('');
                            IndicoUI.Dialogs.Util.error(error);
                        }
                        else{
                            self.persistentUserEnabled = true;
                            self._getExportURLs('progressPersistentSignatures');
                        }
                    });
        }

        else{
            self.createKey(true, '#progressPersistentSignatures');
        }
    }


}, function(apiMode, persistentUserEnabled, persistentAllowed, apiActive, userLogged, setURLsFunction, getURLsMethod, getURLsParams, requestURLs){

    this.apiMode = any(apiMode, 0);
    this.persistentUserEnabled = any(persistentUserEnabled, false);
    this.persistentAllowed = any(persistentAllowed, false);
    this.apiActive = any(apiActive, false);
    this.userLogged = any(userLogged, false);
    this.setURLsFunction = setURLsFunction;
    this.getURLsMethod = any(getURLsMethod, "");
    this.getURLsParams = any(getURLsParams, {});
    this.requestURLs = any(requestURLs, {});
    this.agreementMethod = "";

    var self = this;

    self.setURLsFunction(self.requestURLs);

    switch(self.apiMode){
        case 0://API_MODE_KEY
            $('#publicLinkWrapper').append($("#publicLink")).show();
            if(self.userLogged){
                if (self.apiActive){
                    self._showAuthLink();
                } else{
                    self._showAgreement('#agreementApiKey');
                }
            }
            break;
        case 1://API_MODE_ONLYKEY
            if(self.userLogged){
                if (self.apiActive){
                    $('#publicLinkWrapper').append($("#publicLink")).show();
                    self._showAuthLink();
                } else{
                    $('#authLinkWrapper').append($("#agreementApiKey"));
                }
            }
            break;
        case 2://API_MODE_SIGNED
            $('#publicLinkWrapper').append($("#publicLink")).show();
            if(self.userLogged){
                if(self.apiActive){
                    self._checkPersistentEnabled(false);
                } else{
                    self._showAgreement('#agreementApiKey');
                    if(self.persistentAllowed){
                        $('#authLinkWrapper').append($("#agreementPersistentSignatures"));
                    }
                }
            }
            else {
                $('#extraInformation').insertAfter('#publicLinkWrapper');
            }

            break;
        case 3://API_MODE_ONLYKEY_SIGNED
            if(self.userLogged){
                if(self.apiActive){
                    $('#publicLinkWrapper').append($("#publicLink")).show();
                    self._checkPersistentEnabled(false);
                } else{
                    $('#publicLinkWrapper').append($("#agreementApiKey")).show();
                    if(self.persistentAllowed){
                        $('#authLinkWrapper').append($("#agreementPersistentSignatures"));
                    }
                }
            }
            break;
        case 4://API_MODE_ALL_SIGNED
            if(self.userLogged){
                if(self.apiActive){
                    self._checkPersistentEnabled(true);
                } else{
                    $('#authLinkWrapper').append($("#agreementApiKey"));
                    if(self.persistentAllowed){
                        $('#authLinkWrapper').append($("#agreementPersistentSignatures"));
                    }
                }
            }            break;
    };

});


$(function() {

    $('#exportIcal').qtip({

        style: {
            width: '300px',
            classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-popup',
            tip: {
                corner: true,
                width: 20,
                height: 15
            }
        },
        position: {
            my: 'top center',
            at: 'bottom center'
        },
        content: $('#icalExportPopup'),
        show: {
            event: 'click',
            effect: function() {
                $(this).show('slide', {direction: 'up'});
            },
            target: $('#exportIcal')
        },
        hide: {
            event: 'unfocus click',
            fixed: true,
            effect: function() {
                $(this).fadeOut(300);
            }
        },
        events: {
            render: function(event, api) {
                $('#publicLink, #authLink').click(function(e){
                    $(this).select();
                });

                $('#agreementButtonPersistent').click(function(e) {
                    $('#progressPersistentSignatures').html($(progressIndicator(true, false).dom));
                    exportIcal.enablePersistentSignatures();
                });

                $('#agreementButtonKey').click(function(e) {
                    exportIcal.createKey(false, '#progressPersistentKey');
                });

                $('#agreeCheckBoxKey').click(function(e) {
                    if(this.checked){
                        $('#agreementButtonKey').removeAttr("disabled");
                    }else{
                        $('#agreementButtonKey').attr("disabled","disabled");
                    }
                });
                $('#agreeCheckBoxPersistent').click(function(e) {
                    if(this.checked){
                        $('#agreementButtonPersistent').removeAttr("disabled");
                        $('#agreeCheckBoxKey')[0].checked = true;
                    }else{
                        $('#agreementButtonPersistent').attr("disabled","disabled");
                    }

                });

            },
        }
    });
});