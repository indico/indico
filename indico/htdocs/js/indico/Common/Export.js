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
                                    self._postAcceptAgreements('#agreementApiKey'+self.id);
                                }
                                break;
                            case 1:
                                if(self.apiActive){
                                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                                    self._postAcceptAgreements('#agreementApiKey'+self.id);

                                }
                                break;

                            case 2:
                                if(self.apiActive){
                                    $('#agreementApiKey').hide();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        self._postAcceptAgreements('#agreementPersistentSignatures'+self.id);
                                    }
                                }
                                break;

                            case 3:
                                if(self.apiActive){
                                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        self._postAcceptAgreements('#agreementPersistentSignatures'+self.id);
                                    }
                                    else {
                                        $('#extraInformation'+self.id).insertAfter('#publicLinkWrapper'+self.id);
                                    }
                                    $('#agreementApiKey'+self.id).hide();
                                }

                                break;

                            case 4:
                                if(self.apiActive){
                                    $('#agreementApiKey'+self.id).hide();
                                    if(self.persistentUserEnabled && self.persistentAllowed || !self.persistentAllowed){
                                        $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                                        self._postAcceptAgreements('#agreementPersistentSignatures'+self.id);
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
            if(publicLink) $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
            self._showAuthLink();
        }else{
            $('#authLinkWrapper'+self.id).append($("#agreementPersistentSignatures"+self.id)).show();
        }
    },

    _postAcceptAgreements: function(targetAgreement){
        $('#authLinkWrapper'+this.id).append($("#authLink"+this.id)).show();
        $('#extraInformation'+this.id).insertAfter('#authLinkWrapper'+this.id);
        $(targetAgreement).hide();
    },

    _showAuthLink: function(){
        $('#authLinkWrapper'+this.id).append($("#authLink"+this.id)).show();
        $('#extraInformation'+this.id).insertAfter('#authLinkWrapper'+this.id);
    },

    _showAgreement: function(agreementTarget){
        $('#extraInformation').insertAfter('#publicLinkWrapper'+this.id);
        $('#authLinkWrapper'+this.id).append($(agreementTarget)).show();
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
                        self._getExportURLs(progressTarget);
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
    },

    showContent: function(){
        var self = this;
        self.setURLsFunction(self.requestURLs);
        switch(self.apiMode){
        case 0://API_MODE_KEY
            $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
            if(self.userLogged){
                if (self.apiActive){
                    self._showAuthLink();
                } else{
                    self._showAgreement('#agreementApiKey'+self.id);
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 1://API_MODE_ONLYKEY
            if(self.userLogged){
                if (self.apiActive){
                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                    self._showAuthLink();
                } else{
                    $('#authLinkWrapper'+self.id).append($("#agreementApiKey"+self.id)).show();
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 2://API_MODE_SIGNED
            $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
            if(self.userLogged){
                if(self.apiActive){
                    self._checkPersistentEnabled(false);
                } else{
                    self._showAgreement('#agreementApiKey'+self.id);
                    if(self.persistentAllowed){
                        $('#authLinkWrapper'+self.id).append($("#agreementPersistentSignatures"+self.id)).show();
                    }
                }
            }
            else {
                $('#extraInformation'+self.id).insertAfter('#publicLinkWrapper'+self.id);
            }
            $('#iCalSeparator'+self.id).show();
            break;
        case 3://API_MODE_ONLYKEY_SIGNED
            if(self.userLogged){
                if(self.apiActive){
                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                    self._checkPersistentEnabled(false);
                } else{
                    $('#publicLinkWrapper'+self.id).append($("#agreementApiKey"+self.id)).show();
                    if(self.persistentAllowed){
                        $('#authLinkWrapper'+self.id).append($("#agreementPersistentSignatures"+self.id)).show();
                    }
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
        case 4://API_MODE_ALL_SIGNED
            if(self.userLogged){
                if(self.apiActive){
                    self._checkPersistentEnabled(true);
                } else{
                    $('#authLinkWrapper'+self.id).append($("#agreementApiKey"+self.id));
                    if(self.persistentAllowed){
                        $('#authLinkWrapper'+self.id).append($("#agreementPersistentSignatures"+self.id));
                    }
                }
                $('#iCalSeparator'+self.id).show();
            }
            break;
    };

    }


}, function(apiMode, persistentUserEnabled, persistentAllowed, apiActive, userLogged, setURLsFunction, getURLsMethod, getURLsParams, requestURLs, id){

    this.apiMode = any(apiMode, 0);
    this.persistentUserEnabled = any(persistentUserEnabled, false);
    this.persistentAllowed = any(persistentAllowed, false);
    this.apiActive = any(apiActive, false);
    this.userLogged = any(userLogged, false);
    this.setURLsFunction = setURLsFunction;
    this.getURLsMethod = any(getURLsMethod, "");
    this.getURLsParams = any(getURLsParams, {});
    this.requestURLs = any(requestURLs, {});
    this.id = any(id,"");
    this.agreementMethod = "";

    var self = this;

    self.showContent();

});

var createExportPopup = function(elementId, exportId, eventType){

    $("#"+elementId).qtip({

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
            at: 'bottom center',
        },
        content: $('#icalExportPopup'+exportId),
        show: {
            event: eventType,
            effect: function() {
                $(this).show('slide', {direction: 'up'});
            },
            target: $("#"+elementId),
            ready: true
        },
        hide: {
            event: 'unfocus click',
            fixed: true,
            effect: function() {
                $(this).fadeOut(300);
            }
        },
    });

};

var exportPopups= {};

$(function() {

    $('body').delegate('.exportIcal','click',function(e){
        createExportPopup(this.id, this.dataset.id ,e.type);
    });

    $('body').delegate('.apiURL','click',function(e){
        $(this).select();
    });

    $('body').delegate('.agreementButtonPersistent','click',function(e){
        $('#progressPersistentSignatures'+this.dataset.id).html($(progressIndicator(true, false).dom));
        exportPopups[this.dataset.id].enablePersistentSignatures();
    });

    $('body').delegate('.agreementButtonKey','click',function(e){
        exportPopups[this.dataset.id].createKey(false, '#progressPersistentKey'+this.dataset.id);
    });

    $('body').delegate('.agreeCheckBoxKey','click',function(e){
        if(this.checked){
            $('#agreementButtonKey'+this.dataset.id).removeAttr("disabled");
        }else{
            $('#agreementButtonKey'+this.dataset.id).attr("disabled","disabled");
        }
    });

    $('body').delegate('.agreeCheckBoxPersistent','click',function(e){
        if(this.checked){
            $('#agreementButtonPersistent'+this.dataset.id).removeAttr("disabled");
            $('#agreeCheckBoxKey'+this.dataset.id)[0].checked = true;
        }else{
            $('#agreementButtonPersistent'+this.dataset.id).attr("disabled","disabled");
        }
    });
});