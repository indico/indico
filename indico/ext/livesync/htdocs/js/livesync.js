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
         _submit: function(info, addMode) {

             var self = this;

             if(this.parameterManager.check() && this.pmExtra.check()) {
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
                 new AlertPopup($T("Warning"), $T("Please fill in the missing parameters")).open();
             }
         },

         draw: function() {
             var self = this;

             this.parameterManager = new IndicoUtil.parameterManager();
             this.pmExtra = new IndicoUtil.parameterManager();

             var selectType = Widget.select(this._availableTypes);
             var idField = new RealtimeTextBox();

             if (!this.fullyEditable) {
                 $(selectType.dom).attr('disabled', 'disabled');
                 idField.disable();
             } else {
                 this.parameterManager.add(selectType, 'text', false);
                 this.parameterManager.add(idField, 'text', false);
             }

             var mainContent = IndicoUtil.createFormFromMap([
                 [$T('Type'),
                  $B(selectType,
                     this.info.accessor('type'))],
                 [$T('Agent ID'),
                  $B(idField,
                     this.info.accessor('id')).draw()],
                 [$T('Name'),
                 $B(this.parameterManager.add(new RealtimeTextBox(), 'text', false),
                    this.info.accessor('name')).draw()],
                 [$T('Description'),
                  $B(this.parameterManager.add(new RealtimeTextArea({}), 'text', false),
                    this.info.accessor('description')).draw()]]
             );

             var specificOptions = bind.element(
                 Html.tbody({}),
                 this._extraOptions,
                 function(option) {
                     return Html.tr(
                         {},
                         Html.td("popUpLabel", option.get()),
                         Html.td({},
                                 $B(self.pmExtra.add(new RealtimeTextBox(), 'text', false),
                                    self.info.get('specific').accessor(option.key)).draw()));
                 });

             if (this.fullyEditable) {
                 selectType.observe(function(agentType) {
                     self.pmExtra.clear();
                     self.info.set('specific', $O())
                     self._resetForm(agentType);
                 });
             }

             return this.ExclusivePopupWithButtons.prototype.draw.call(this, $('<div></div>').append(mainContent, $('<table></table>').append($(specificOptions.dom))));
         },

         _getButtons: function() {
             var self = this;
             return [
                 [this.fullyEditable ? $T('Add') : $T('Save'), function() {
                     self._submit(self.info, self.fullyEditable);
                 }]
             ];
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
