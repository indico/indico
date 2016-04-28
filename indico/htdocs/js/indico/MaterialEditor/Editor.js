/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

type("UploadTemplateDialog", ["ExclusivePopupWithButtons"], {

    _getButtons: function() {
        var self = this;
        return [
            [$T('Upload'), function() {
                if (self.pm.check()) {
                    self.killProgress = IndicoUI.Dialogs.Util.progress($T('Uploading...'));
                    $(self.form.dom).submit();
                }
            }],
            [$T('Cancel'), function() {
                self.close();
            }]
        ];
    },

    _fileUpload: function() {
        var self = this;
        var pm = self.pm = new IndicoUtil.parameterManager();
        var uploadType = Html.input('hidden', {name: 'uploadType'});
        var selector = this._showFormatChooser(pm);
        var file = Html.input('file', {name: 'file'});
        var description = Html.textarea({name: 'description'});
        var name = Html.edit({name: 'name'});

        uploadType.set('file');

        pm.add(selector, 'text', false);
        pm.add(file, 'text', false);
        pm.add(description, 'text', true);
        pm.add(name, 'text', true);

        this.form = Html.form({
                            method: 'post',
                            id: Html.generateId(),
                            action: build_url(this.uploadAction, this.args),
                            enctype: 'multipart/form-data',
                            encoding: 'multipart/form-data'
                        },
                        Html.input('hidden', {name: 'conference'}, this.args.conference),
                        IndicoUtil.createFormFromMap(
                            [
                                [$T('Name'), name],
                                [$T('Type'), selector],
                                [$T('File'), file],
                                [$T('Description'), description]
                            ]).get(),
                        uploadType);

        $(this.form.dom).ajaxForm({
            dataType: 'json',
            iframe: true,
            complete: function(){
                self.killProgress();
            },
            success: function(resp){
                if (resp.status == "ERROR") {
                    IndicoUtil.errorReport(resp.info);
                } else {
                    self.close();
                    self.onUpload(resp.info);
                }
            }
        });

        return Html.div({}, this.form);
},

    _showFormatChooser: function(pm) {
        var self = this;
        var select = Html.select({name: 'format'});
        var text = Html.edit({name: 'format'});

        var chooser = new Chooser(new Lookup({
            select: function() {
                pm.remove(text);
                pm.add(select);

                return Html.div({}, bind.element(select, $L(self.types),
                                          function(value) {
                                              return Html.option({'value': value}, value);
                                          }),
                         " ",
                         $T("or"),
                         " ",
                         Widget.link(command(function() {
                             chooser.set('write');
                         }, $T("other"))));
            },

            write: function() {
                bind.detach(select);
                pm.remove(select);
                pm.add(text, 'text');
                return Html.div({}, text,
                                " ",
                               $T("or"),
                               " ",
                                Widget.link(command(function() {
                                    chooser.set('select');
                                }, $T("select from list"))));
            }
        }));
        chooser.set('select');

        return Widget.block(chooser);
    },

    draw: function() {
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._fileUpload());
    }
}, function(title, args, width, height, types, uploadAction, onUpload) {
    this.title = title;
    this.width = width;
    this.height = height;
    this.types = types;
    this.uploadAction = uploadAction;
    this.onUpload = onUpload;

    this.args = clone(args);
    this.ExclusivePopupWithButtons($T(title));
});



function contains(a, obj){
    for(var i = 0; i < a.length; i++) {
      if(a[i] === obj){
        return true;
      }
    }
    return false;
}

