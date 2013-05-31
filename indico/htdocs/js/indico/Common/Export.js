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
                                    $('#agreementApiKey'+self.id).hide();
                                    if(self.persistentUserEnabled && self.persistentAllowed){
                                        self._postAcceptAgreements('#agreementPersistentSignatures'+self.id);
                                    }
                                }
                                break;

                            case 3:
                                if(self.apiActive){
                                    $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                                    if(self.persistentUserEnabled && self.persistentAllowed){
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
                                    if(self.persistentUserEnabled && self.persistentAllowed){
                                        $('#publicLinkWrapper'+self.id).append($("#publicLink"+self.id)).show();
                                        self._postAcceptAgreements('#agreementPersistentSignatures'+self.id);
                                    }
                                }
                                break;
                    };
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
            indicoRequest('user.togglePersistentSignatures', {userId: self.userId},
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

}, function(apiMode, persistentUserEnabled, persistentAllowed, apiActive, userLogged, setURLsFunction, getURLsMethod, getURLsParams, requestURLs, id, userId){

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
    this.userId = any(userId, "");

    var self = this;

    self.showContent();

});


var exportPopups= {};

$(document).ready(function() {

    $(".exportIcal").on('menu_select', function() {
        var $button = $(this);

        if ($button.hasClass('open')) {
            return;
        } else {
            $button.addClass('open');

            $("<a/>").qtip({
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
                hide: {
                    event: 'unfocus',
                    fixed: true,
                    target: $button,
                    effect: function() {
                        $(this).fadeOut(300);
                        $button.removeClass('open');
                    }
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