/*

type("CategoryEventSelectionWidget", ["IWidget"],
     {
         draw: function() {
             var categoryChooser = new CategoryChooser({id: '0'},
                 function(categ) {
                     alert(Json.write(categ));
                 });
             return Widget.link(command(function() {
                 categoryChooser.open();
             }, "choose..."));
         }

     },
     function() {
     });

FUTURE: use category selector (need to be browsable first)

*/

type("UpcomingEventFavoritesList", ["RemoteListWidget"],
     {
         _removeElem: function(elemType, elemId) {
             var self = this;

             var info = {
                 type: elemType,
                 id: elemId
             };

             var killProgress = IndicoUI.Dialogs.Util.progress();

             indicoRequest('upcomingEvents.admin.removeObservedObject', info,
                           function(result, error) {
                               if (!error) {
                                   self.set(
                                       (elemType=="category"?"cat":"")+elemId, null);
                                   killProgress();
                               } else {
                                   IndicoUtil.errorReport(error);
                                   killProgress();
                               }
                           });
         },

         _addElement: function(element) {
             if (element.object.name) {
                 // category
                 this.set("cat"+element.object.id, element);
             } else {
                 // event
                 this.set(element.object.id, element);
             }
         },

         _drawItem: function(pair) {
             var elem = pair.get();
             var self = this;

             if (elem.object.name) {
                 return Html.span({}, "Cat. \"" + elem.object.name + '\" ( weight ' + elem.weight + ', ' + elem.delta +' days )', Widget.link(command(function() {
                     self._removeElem("category", elem.object.id);
                 }, IndicoUI.Buttons.removeButton())));
             } else {
                 return Html.span({}, elem.object.title + ' ( weight ' + elem.weight + ', delta ' + elem.delta + ' )', Widget.link(command(function() {
                     self._removeElem("event", elem.object.id);
                 }, IndicoUI.Buttons.removeButton())));
             }
         }
     },
     function() {
         this.RemoteListWidget("CategoryList", 'upcomingEvents.admin.getEventCategoryList', {});
     });

type("CategoryEventAddDialog", ["ExclusivePopupWithButtons"],
     {
         draw: function() {
             var self = this;

             var selection = Html.select({},
                 Html.option({value: 'category'}, "Category"),
                 Html.option({value: 'event'}, "Event"));

             this.info = new WatchObject();
             this.info.set('type', 'category');

             var form = IndicoUtil.createFormFromMap([
                 ["Type", $B(selection, this.info.accessor('type'))],
                 ["Id", $B(Html.edit(), this.info.accessor('id'))],
                 ["Weight (float)", $B(Html.edit(), this.info.accessor('weight'))],
                 ["Advertisement time (days)", $B(Html.edit(), this.info.accessor('delta'))]]);

             return this.ExclusivePopupWithButtons.prototype.draw.call(this, Html.div({}, form));
         },

         _getButtons: function() {
             var self = this;
             return [
                 [$T('Add'), function() {
                     var killProgress = IndicoUI.Dialogs.Util.progress();
                     indicoRequest('upcomingEvents.admin.addObservedObject', self.info, function(result, error) {
                         if (!error) {
                             self.targetList._addElement(result);
                             self.close();
                             killProgress();
                         }
                         else {
                             IndicoUtil.errorReport(error);
                             killProgress();
                         }
                     });
                 }],
                 [$T('Cancel'), function() {
                     self.close();
                 }]
             ];
         }
     },
     function(targetList) {
         var self = this;
         this.targetList = targetList;
         this.ExclusivePopupWithButtons("Add Category/Event", function() {
             return true;
         });
     });

type("UpcomingEventFavoritesWidget", ["IWidget"],
     {
         draw: function() {
             var listWidget = new UpcomingEventFavoritesList();
             return Html.div({},
                             Html.div('CategoryEventListDiv', listWidget.draw()),
                             Html.div({}, Widget.button(command(
                                 function() {
                                     var dialog = new CategoryEventAddDialog(listWidget);
                                     dialog.open();
                                 }, "Add"
                             )))
                            );
         }
     },
     function() {
     }
    );