// -*- coding: utf-8 -*-
//
//
// This file is part of Indico.
// Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
//
// CDS Indico is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// CDS Indico is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

function activateAgentText(agentId) {
    return Html.div(
        {style: {width: '350px'}},
        $T('Activation is done in two simple steps.'),
        $T('The first step requires the remote service to be synchronized with ' +
           'Indico. In order to do so, you should run the following command:'),
        Html.div({style: {fontFamily: 'monospace',
                          marginTop: '10px',
                          marginBottom: '10px'}},
                 'indico_livesync agent ' + agentId + ' export'),
        Html.div({}, $T("When it finishes, press the 'activate' button in the agent list.")),
        Html.div({}, $T("Press 'Cancel' if you don't want to proceed with the activation.")))
};

function agentRequest(method, agentId) {
    indicoRequest(
        method,
        {'id': agentId},
        function(result, error) {
            if (error) {
                IndicoUtil.errorReport(error);
            } else {
                window.location.reload();
            }
        });
}

type("AgentModificationDialog", ["ExclusivePopupWithButtons"],
     {
         _submit: function(info, pm, pmExtra, addMode) {

             var self = this;

             if(pm.check() && pmExtra.check()) {
                 indicoRequest(
                     addMode?'livesync.addAgent':'livesync.editAgent',
                     info,
                     function(result, error) {
                         if (error) {
                             IndicoUtil.errorReport(error);
                         } else {
                             window.location.reload();
                         }
                     });
             } else {
                 alert($T("Please fill in the missing parameters"));
             }
         },

         draw: function() {
             var self = this;

             var parameterManager = new IndicoUtil.parameterManager();
             var pmExtra = new IndicoUtil.parameterManager();

             var selectType = Widget.select(this._availableTypes);
             var idField = new RealtimeTextBox();

             if (!this.fullyEditable) {
                 selectType.disable();
                 idField.disable();
             } else {
                 parameterManager.add(selectType, 'text', false);
                 parameterManager.add(idField, 'text', false);
             }

             var mainContent = IndicoUtil.createFormFromMap([
                 [$T('Type'),
                  $B(selectType,
                     this.info.accessor('type'))],
                 [$T('Agent ID'),
                  $B(idField,
                     this.info.accessor('id')).draw()],
                 [$T('Name'),
                 $B(parameterManager.add(new RealtimeTextBox(), 'text', false),
                    this.info.accessor('name')).draw()],
                 [$T('Description'),
                  $B(parameterManager.add(new RealtimeTextArea({}), 'text', false),
                    this.info.accessor('description')).draw()]]
             );

             var button = Html.input("button", {}, this.fullyEditable?$T("Add"):$T("Save"));
             var buttonDiv = Html.div({}, button);

             button.observeClick(function() {
                 self._submit(self.info, parameterManager, pmExtra, self.fullyEditable);
             });

             var specificOptions = bind.element(
                 Html.tbody({}),
                 this._extraOptions,
                 function(option) {
                     return Html.tr(
                         {},
                         Html.td("popUpLabel", option.get()),
                         Html.td({},
                                 $B(pmExtra.add(new RealtimeTextBox(), 'text', false),
                                    self.info.get('specific').accessor(option.key)).draw()));
                 });

             if (this.fullyEditable) {
                 selectType.observe(function(agentType) {
                     pmExtra.clear();
                     self.info.set('specific', $O())
                     self._resetForm(agentType);
                 });
             }

             return this.ExclusivePopupWithButtons.prototype.draw.call(
                 this, Html.div(
                     {},
                     mainContent,
                     Html.table({}, specificOptions)),
                 buttonDiv, {}, { padding : pixels(0) });
         }

     });


type("AddAgentDialog", ["AgentModificationDialog"],
     {

         _resetForm: function(agentType) {
             this._extraOptions.clear()
             this._extraOptions.update(this._allExtraOptions[agentType])

             var self = this;
             each(this.info, function(value, key) {
                 if (key != 'type' && key != 'specific') {
                     self.info.set(key, undefined);
                 }
             });

             each(this.info.get('specific'), function(value, key) {
                 self.info.set(key, undefined);
             });

             this.info.set('type', agentType);
         },

         postDraw: function() {
             var defaultType = keys(this._allExtraOptions)[0];
             this._resetForm(defaultType);
             this.ExclusivePopupWithButtons.prototype.postDraw.call(this);
         }

     },
     function(availableTypes, allExtraOptions) {
         var self = this;

         this.info = $O({'specific': $O()});
         this.fullyEditable = true;

         this._availableTypes = availableTypes;
         this._extraOptions = $O(allExtraOptions[keys(this._allExtraOptions)[0]]);

         this._allExtraOptions = allExtraOptions;

         this.ExclusivePopupWithButtons($T("Add New Agent"),
                                        function() {
                                            self.close();
                                        });
     });


type("EditAgentDialog", ["AgentModificationDialog"],
     {
     },
     function(availableTypes, extraOptions, info) {

         var self = this;
         this.info = watchize(info)

         this._availableTypes = availableTypes;
         this._extraOptions = extraOptions;

         this.ExclusivePopupWithButtons($T("Edit Agent"),
                                        function() {
                                            self.close();
                                        });
     });
