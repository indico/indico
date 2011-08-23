type("ApplyForParticipationPopup", ["ServiceDialogWithButtons"], {
    _success: function(response) {
        this.onSuccess(response);
    },

    _save: function(response) {
        var self = this;
        if(self.parameterManager.check()){
            self.request(self.userData);
        }
    },

    _drawButtons: function(){
        var self = this;
        var saveButton = Html.input('button', {style: {marginRight: pixels(3)}}, $T('Ok'));
        var cancelButton = Html.input('button', {style: {marginLeft: pixels(3)}}, $T('Cancel'));
        saveButton.observeClick(function(){
            self._save();
        });
        cancelButton.observeClick(function(){
            self.close();
        });
       return Html.div({}, saveButton, cancelButton);
    },

    _drawUserEditable: function() {
        var self = this;
        return IndicoUtil.createFormFromMap(
                [
                 [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({value:'Mr.'}, $T("Mr.")), Html.option({value:'Mrs.'}, $T("Mrs.")), Html.option({value:'Ms.'}, $T("Ms.")), Html.option({value:'Dr.'}, $T("Dr.")), Html.option({value:'Prof.'}, $T("Prof."))), self.userData.accessor('title'))],
                 [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'text', false), self.userData.accessor('surName'))],
                 [$T('First Name'), $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'text', false), self.userData.accessor('name'))],
                 [$T('Affiliation'), $B(Html.edit({style: {width: '200px'}}), self.userData.accessor('affiliation'))],
                 [$T('Email'),  $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'email', true), self.userData.accessor('email'))],
                 [$T('Address'), $B(Html.textarea({style: {width: '200px'}}), self.userData.accessor('address'))],
                 [$T('Telephone'), $B(Html.edit({style: {width: '150px'}}), self.userData.accessor('phone'))],
                 [$T('Fax'), $B(Html.edit({style: {width: '150px'}}), self.userData.accessor('fax'))],
             ]);
    },

    _drawUserNotEditable: function() {
        var self = this;
        return IndicoUtil.createFormFromMap(
                [
                 [$T('Title'), self.userData.get("title")],
                 [$T('Last Name'),self.userData.get("surName")],
                 [$T('First Name'), self.userData.get("name")],
                 [$T('Email'),self.userData.get("email")],
                 [$T('Address'),self.userData.get("address")],
                 [$T('Affiliation'),self.userData.get("affiliation")],
                 [$T('Telephone'),self.userData.get("phone")],
                 [$T('Fax'),self.userData.get("fax")]
             ]);
    },

    draw: function() {
        var self = this;
        self.parameterManager = new IndicoUtil.parameterManager();
        var tabWidget = null;
        if(this.allowEdit){
            tabWidget = self._drawUserEditable();
        }
        else{
            tabWidget = self._drawUserNotEditable();
        }
        return this.ServiceDialogWithButtons.prototype.draw.call(this, tabWidget, this._drawButtons());
    }
},

    function(confId, method, title, userData, onSuccess, allowEdit) {
        this.onSuccess = any(onSuccess,positive);
        this.confId = confId;
        this.userData = $O(userData);
        this.allowEdit = any(allowEdit, true);
        var self = this;
        self.userData.set("confId",self.confId);
        this.ServiceDialogWithButtons(Indico.Urls.JsonRpcService, method, userData, title, function() {self.close();});
        self.open();
    }
);


type("BasicEmailPopup", ["ExclusivePopupWithButtons"],{

    _drawButtons: function(){
        var self = this;
        var sendButton = Html.input('button', null, $T("Send"));
        sendButton.observeClick(function(){
            self.sendFunction();
        });
        var cancelButton = Widget.button(command(function() {self.close();}, $T("Cancel")));
        var buttonDiv = Html.div({style:{textAlign:"center"}}, sendButton, cancelButton)
        return buttonDiv;
    },

    _drawRTWidget: function(){

        var self = this;
        // Text editor with default message
        self.rtWidget = new ParsedRichTextEditor(700, 400, 'IndicoMinimal');
        self.rtWidget.set(self.defaultText);
    },

    _drawTop: function(){
        var self = this;
        return Html.div({}, self._drawFromAddress(), self._drawToAddress(), self._drawSubject());
    },

    _drawWidget: function(){
        var self = this;
        self._drawRTWidget();
        return Html.div({}, self._drawTop(), self.rtWidget.draw(), self._drawLegends());
    },

    _drawLegends: function(){
        var self = this;
        if(_.size(self.legends) == 0){
            return null;
        }
        var legendFields = [];
        for(legend in self.legends){
            legendFields.push(Html.tr({}, Html.td({}, "{"+legend+"} :"), Html.td({}, self.legends[legend])));
        }
        return Html.div({style:{marginLeft: '20px',
                         fontStyle:'italic',
                         color:'gray'}
                  },
                  Html.div({style:{fontWeight:'bold'}}, $T("Legend:")),
                  Html.table({},legendFields));
    },

    draw: function(){
        var self = this;

        return this.ExclusivePopupWithButtons.prototype.draw.call(
                self,
                self._drawWidget(),
                self._drawButtons()
                );
    }
},
function(title, confTitle, confId, subject, defaultText, legends){
    var self = this;
    self.confTitle = confTitle;
    self.confId = confId;
    self.defaultText = any(defaultText,"");
    self.subject = new WatchObject();
    $B(self.subject.accessor(), subject);
    self.legends = any(legends,{});

    this.ExclusivePopupWithButtons(title);
}
);