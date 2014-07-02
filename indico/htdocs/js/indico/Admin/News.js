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

type("NewsList", ["WatchList"],
    {
        renderNewsItem: function (item) {
            return item.draw();
        },

        addItem: function() {
            var addNews = new NewsItem('edit', this);
            this.insert(addNews, '0');
        },

        deleteNewsItem: function(item) {
            var self = this;
            var killProgress = IndicoUI.Dialogs.Util.progress();
            jsonRpc(Indico.Urls.JsonRpcService, 'news.delete', {'id': item.id},
                    function(response, error){
                        if (exists(error)) {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        }
                        else {
                            killProgress();
                            self.remove(item);
                        }
                    });
        }
    },

    function(newslist, web_container, newsTypesList) {
        this.WatchList();
        this.newsTypesList = newsTypesList;
        var self = this;
        each(newslist, function(item){
            self.append(new NewsItem('display', self, item));
        });
        $B($E(web_container), this, this.renderNewsItem);
    }

);


type("NewsItem", ["ServiceWidget"],
    {

        _createResource: function() {
            var params = {"title": this.titleField.get(), "type": this.typeField.get(), "content": this.content.get()};
            this.request(params);
        },

        _saveResource: function() {
            var params = {"id":this.id, "title": this.titleField.get(), "type": this.typeField.get(), "content": this.content.get()};
            var self = this;
            var killProgress = IndicoUI.Dialogs.Util.progress();
            if(self.content.clean())
                jsonRpc(Indico.Urls.JsonRpcService, 'news.save', params,
                        function(response, error){
                            if (exists(error))
                                IndicoUtil.errorReport(error);
                            else
                                self._success(response);
                        });
            killProgress()
        },

        _success: function(response) {
            this.creationDate = response.creationDate;
            this.title = response.title;
            this.type = response.type;
            this.text = response.text;
           this.id = response.id;

            this.chooser.set('display');
        },

        draw: function() {
            var self = this;

            var titleField = Html.input('text',{'className':'newsEditTitle'},'Write a title');
            var typeField = Widget.select(self.parentList.newsTypesList);
            typeField.set('general');

            this.titleField = titleField;
            this.typeField = typeField;

            var saveButton = null;
            if (self.id) {
                this.titleField.set(self.title);
                this.typeField.set(self.type);
                saveButton = Widget.button(command(function (){
                    self._saveResource();
                }, "Save"));
            }else {
                saveButton = Widget.button(command(function (){
                    self._createResource();
                }, "Save"));
            }

            var cancelButton = Widget.button(command(function (){
               if (self.id) {
                    self.chooser.set('display');
               } else {
                   self.parentList.remove(self);
               }
            }, "Cancel"));

            this.chooser = new Chooser(new Lookup({
                edit: function() {
                   var content = new ParsedRichTextEditor(600,400);
                   self.content = content;

                   if (self.id) {
                       content.set(self.text);
                   }

                    return Html.div("newsItemEdit", titleField, typeField, content.draw(),
                                                   saveButton, cancelButton); },
                display: function() {
                    var newsItemContentDiv = Html.div("newsItemContent");
                    newsItemContentDiv.dom.innerHTML = self.text;
                    return Html.div("newsItem",
                                    Html.div("newsItemOptions",
                                            Widget.link(command(function (){
                                                self.parentList.deleteNewsItem(self);
                                            }, IndicoUI.Buttons.removeButton())),
                                            Widget.link(command(function (){
                                                self.chooser.set('edit');
                                            }, IndicoUI.Buttons.editButton()))),
                                    Html.div("newsItemDate", IndicoUtil.formatJsonDate(self.creationDate)),
                                    Html.div("newsItemTitle", self.title + " (" + self.type + ")"),
                                    newsItemContentDiv
                     );
                }
            }));

            this.chooser.set(this.choice);

            return this.ServiceWidget.prototype.draw.call(this, Widget.block(this.chooser));
        }
    },

    function(choice, parentList, item) {
        this.choice = choice;
        this.parentList = parentList;
        if (item) {
            extend(this, item);
        }
        this.ServiceWidget(Indico.Urls.JsonRpcService, 'news.add', {});
    }
);
