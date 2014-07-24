/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

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

    _getButtons: function(){
        var self = this;
        return [
            [$T('OK'), function() {
                self._save();
            }, true],
            [$T('Cancel'), function(){
                self.close();
            }]
        ]
    },

    _drawUserEditable: function() {
        var self = this;
        return IndicoUtil.createFormFromMap(
                [
                 [$T('Title'), $B(Html.select({}, Html.option({}, ""), Html.option({value:'Mr.'}, $T("Mr.")), Html.option({value:'Mrs.'}, $T("Mrs.")), Html.option({value:'Ms.'}, $T("Ms.")), Html.option({value:'Dr.'}, $T("Dr.")), Html.option({value:'Prof.'}, $T("Prof."))), self.userData.accessor('title'))],
                 [$T('Family Name'), $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'text', false), self.userData.accessor('surName'))],
                 [$T('First Name'), $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'text', false), self.userData.accessor('name'))],
                 [$T('Affiliation'), $B(Html.edit({style: {width: '200px'}}), self.userData.accessor('affiliation'))],
                 [$T('Email'),  $B(self.parameterManager.add(Html.edit({style: {width: '200px'}}), 'email', false), self.userData.accessor('email'))],
                 [$T('Address'), $B(Html.textarea({style: {width: '200px'}}), self.userData.accessor('address'))],
                 [$T('Telephone'), $B(Html.edit({style: {width: '150px'}}), self.userData.accessor('phone'))],
                 [$T('Fax'), $B(Html.edit({style: {width: '150px'}}), self.userData.accessor('fax'))]
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
        return this.ServiceDialogWithButtons.prototype.draw.call(this, tabWidget);
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

    _getButtons: function(){
        var self = this;
        return [
            [$T('Send'), function() {
                self.sendFunction();
            }],
            [$T('Cancel'), function(){
                self.close();
            }]
        ]
    },

    _drawRTWidget: function(){

        var self = this;
        // Text editor with default message
        self.rtWidget = new ParsedRichTextEditor(700, 400);
        self.rtWidget.set(self.defaultText);
    },

    _drawTop: function(){
        var self = this;
        return Html.div({}, self._drawFromAddress(), self._drawToAddress(), self._drawCCAddress(), self._drawSubject());
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
        for(var legend in self.legends){
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
                self._drawWidget()
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

type("ParticipantsEmailPopup", ["BasicEmailPopup"],{

    _drawFromAddress: function(){
        var self = this;
        var fromField = Html.tr({},
                Html.td({width:"15%"}, Html.span({}, $T("From:"))),
                Html.td({width:"85%"}, Html.span({}, self.from))
        );

        return Html.table({width:"688px"}, fromField);
    },

    _drawToAddress: function(){
        var self = this;
        var toField = Html.tr({},
                Html.td({width:"15%"}, Html.span({}, $T("To:"))),
                Html.td({width:"85%"}, _.values(self.toParticipants).join('; '))
        );

        return Html.table({width:"688px"}, toField);
    },

    _drawCCAddress: function(){
        return null;
    },

    _drawSubject: function(){
        var self = this;
        var subjectField = Html.tr({},
                Html.td({width:"15%"}, Html.span({}, $T("Subject:"))),
                Html.td({width:"85%"}, $B(Html.edit({style: {width: '100%'}}), self.subject.accessor()))
        );
        return Html.table({width:"688px"}, subjectField);
    }

},
    function(title,confTitle, confId, method, toParticipants, from, subject, defaultContent, legends, successHandler){
        var self = this;
        self.toParticipants = toParticipants;
        self.from = from;
        self.toUserIds = any(self.toUserIds,_.keys(toParticipants));
        this.sendFunction=function(){
            var killProgress = IndicoUI.Dialogs.Util.progress($T("Sending email..."));
            jsonRpc(Indico.Urls.JsonRpcService, method,
                {
                    conference : self.confId,
                    userIds: self.toUserIds,
                    subject: self.subject.get(),
                    body: self.rtWidget.get()
                },
                function(result, error){
                    if (error) {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    } else {
                        killProgress();
                        successHandler(result);
                        self.close();
                    }
                }
            );
        };
        this.BasicEmailPopup(title, confTitle, confId, subject, defaultContent, legends);
    }

);

type("ParticipantsInvitePopup", ["ParticipantsEmailPopup"],{

    _drawToAddress: function(){
        var self = this;
        var to = [];
        for (var p in self.toParticipants){
            to.push(self.toParticipants[p].name);
        }
        var toField = Html.tr({},
                Html.td({width:"15%"}, Html.span({}, $T("To:"))),
                Html.td({width:"85%"}, to.join("; "))
        );

        return Html.table({width:"95%"}, toField);
    }
},
    function(title,confTitle, confId, method, toParticipants, from, subject, defaultContent, legends, successHandler){
        this.toUserIds = toParticipants;
        this.ParticipantsEmailPopup(title,confTitle, confId, method, toParticipants, from, subject, defaultContent, legends, successHandler);
    }

);
