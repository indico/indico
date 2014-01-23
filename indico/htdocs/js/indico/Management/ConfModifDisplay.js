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

type("PicList", ["WatchList"], {

    renderItem: function (item) {
        return item.draw();
    },

    addItem: function() {
        var addPic = new PicItem(this, 'edit');
        this.insert(addPic, '0');
    },

    deleteItem: function(item) {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        jsonRpc(Indico.Urls.JsonRpcService, 'event.pic.delete', {'picId': item.id, 'conference':self.confId},
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

     function(picslist, web_container, uploadAction, confId) {
         this.WatchList();
         this.uploadAction = uploadAction;
         this.confId = confId;
         var self = this;
         each(picslist, function(item){
             self.append(new PicItem(self, 'display', item));
         });
         $B($E(web_container), this, this.renderItem);
     }

    );


type("PicItem", ["IWidget"], {

    draw: function() {
        var self = this;

        this.chooser = new Chooser(new Lookup({
            edit: function() {
                var stuffUploadForm = function(inputField, uploadType, submitText) {
                    var killProgress;
                    var form = Html.form({method: 'post', id: Html.generateId(),
                        action: self.parentList.uploadAction,
                        enctype: 'multipart/form-data'});

                    form.append(inputField);

                    form.append(Widget.button(
                        command(function(){
                            killProgress = IndicoUI.Dialogs.Util.progress();
                            $(form.dom).submit();
                        }, submitText)
                    ));

                    $(form.dom).ajaxForm({
                        dataType: 'json',
                        iframe: true,
                        complete: function() {
                            killProgress();
                        },
                        success: function(resp) {
                            if (resp.status == 'ERROR') {
                                IndicoUtil.errorReport(resp.info);
                            }
                            else {
                                self.id = resp.info.id;
                                self.picURL = resp.info.picURL;
                                self.chooser.set('display');
                            }
                        }
                    });

                    return Html.div({}, [form]);
                };

                var fileUpload = stuffUploadForm(Html.input('file', {name: 'file'}), 'file', 'Upload');


                var closeArea = Html.div({},Widget.button(
                    command(function() {
                        self.parentList.remove(self);
                    },"Close")));

                return this.IWidget.prototype.draw.call(this, Html.div({},[fileUpload, closeArea]));
            },
            display: function() {
                var image = Html.img({
                    src: ""+self.picURL,
                    alt: 'Picture preview',
                    title: 'Picture preview',
                    style: {
                        maxWidth: "200px",
                        maxHeight: "100px",
                        border: "0px"
                    }
                });
                var linkToUse = Html.span({style:{color: 'green'}});
                linkToUse.set(Html.a({href:self.picURL}, self.picURL));

                var remButton = Widget.link(command(function (){
                    self.parentList.deleteItem(self);
                }, IndicoUI.Buttons.removeButton()));

                return Html.div({}, [image, linkToUse, remButton]);
            }
        }));

        this.chooser.set(this.choice);

        return Widget.block(this.chooser);

        //path = str(urlHandlers.UHConferencePic.getURL( self._conf))+"&PicId=%s"%str(i)
        //html = html + """<img src=\"%s\" border=\"0\" style=\"width:50px;height:50px;\"></img>"""%path
        //html = html + """<b>Link to use in CSS : <a href=\"%s\" target=\"blank\">%s</a></b>"""%(path,path)
        /*html = html + _("""<form action=\"%s&picId=%s\" method="POST"><input type="submit" class="btn" value="_("X")"></form>""")%(urlHandlers.UHRemovePic.getURL(self._conf),str(i))
                html = html + """<br>"""*/
    }
},

     function(parentList, choice, item) {
         this.choice = choice;
         this.parentList = parentList;
         if (item) {
             extend(this, item);
         }
         //this.ServiceWidget(Indico.Urls.JsonRpcService, 'pics.add', {});
     }
    );
