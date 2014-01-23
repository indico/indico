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

type("RegistrationUploadFile",[],
        {
        draw: function ()
        {
            return this.uploadWidget;
        }

        },
        function(id, valueDisplay, fileName, mandatory){

            var imageRemove = Html.img({
                src: imageSrc("remove"),
                alt: $T('Remove attachment'),
                title: $T('Remove this attachment'),
                id: 'remove'+id,
                style:{marginLeft:'15px', cursor:'pointer', verticalAlign:'bottom'}
            });

            var uploadFileInput = Html.input('file', {id: id, name: id});
            var existingAttachment = Html.div({id:'existingAttachment'+id}, $(valueDisplay)[0],
                                                  imageRemove,
                                                  Html.input("hidden",{id: id, name: id}, fileName));

            $(imageRemove.dom).click(function(e) {
                $E("attachment"+id).set(uploadFileInput);
                if(mandatory){
                    addParam($E(id), 'text', false);
                }
            });

            if(valueDisplay){
                this.uploadWidget = existingAttachment
            } else{
                this.uploadWidget = uploadFileInput;
            }

        });
