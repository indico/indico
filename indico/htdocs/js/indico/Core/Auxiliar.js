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

/**
     @namespace Auxiliar components
    */

var intToStr = function(id) {
    if (IndicoUtil.isInteger(id)) {
        return id+'';
    } else {
        return null;
    }
};

_.mixin({
    move: function (array, fromIndex, toIndex) {
        array.splice(toIndex, 0, array.splice(fromIndex, 1)[0]);
        return array;
    }
});

IndicoUI.Aux = {
    globalChangeHandler: null,

    RichTextEditor: {

        completeHandler: null,

        /**
            * A Plain Text / Rich Text Editor widget
            * @param {Integer} rows Number of rows
            * @param {Integer} cols Number of columns
            * @return An object that conforms Presentation's
            * widget format
            */
        getEditor: function(width, height){


            return function(target, source){

                var accessor = getAccessorDeep(source);
                var field = new RichTextWidget(width, height, '', 'rich');

                var fieldDiv = field.draw();

                field.set(accessor.get());

                $B(target, fieldDiv);

                return {
                    activate: function(){

                        /*                        if (exists(field.editArea.dom.select)) {
                            field.editArea.dom.select();
                        }
                        else {
                            field.editArea.dom.focus();
                        }*/
                    },
                    save: function(){
                        accessor.set(field.get());
                    },
                    stop: function(){
                        field.destroy();
                    }
                };
            };
        }
    },

    updateDateWith: function(element, value){
        var m = value.match(/^([0123]?\d)\/([01]?\d)\/(\d{1,4})\s+([0-2]?\d):([0-5]?\d)$/);
        var date = new Date(m[3], m[2] - 1, m[1], m[4], m[5]);

        if (value === "") {
            element.update("<em>None</em>");
        }
        else {
            element.update(date.toLocaleString());
        }
    },

    dateEditor: function(target, value, onExit){
        var edit = IndicoUI.Widgets.Generic.dateField(this.useTime);
        var exit = function(evt){
            edit.stopObserving('blur', exit);
            onExit(edit.value);
        };

        edit.value = value;
        target.update(edit);
        edit.select();
        edit.observe('blur', exit);
    },

    /**
        * The default "edit" menu, with "Save" and "Cancel" buttons
        * @param {Context} context A Presentation widget context
        * @return A Presentation widget that toggles edit, save and cancel
        * for the widget context
        */
    defaultEditMenu: function(context){
        return Widget.text($B(new Chooser({
            view: [Widget.link(command(context.edit, "(edit)"))],
            edit: [Widget.button(command(context.save, "Save")), Widget.button(command(context.view, "Cancel"))]
        }), context));
    }
};

// from phpjs.org - MIT/GPL licensed
function strcmp (str1, str2) {
    // http://kevin.vanzonneveld.net
    // + original by: Waldo Malqui Silva
    // + input by: Steve Hilder
    // + improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // + revised by: gorthaur
    // * example 1: strcmp( 'waldo', 'owald' );
    // * returns 1: 1
    // * example 2: strcmp( 'owald', 'waldo' );
    // * returns 2: -1
    return ((str1 == str2) ? 0 : ((str1 > str2) ? 1 : -1));
}

// from phpjs.org - MIT/GPL licensed
function strnatcmp (f_string1, f_string2, f_version) {
    // http://kevin.vanzonneveld.net
    // +   original by: Martijn Wieringa
    // + namespaced by: Michael White (http://getsprink.com)
    // +    tweaked by: Jack
    // +   bugfixed by: Onno Marsman
    // -    depends on: strcmp
    // %          note: Added f_version argument against code guidelines, because it's so neat
    // *     example 1: strnatcmp('Price 12.9', 'Price 12.15');
    // *     returns 1: 1
    // *     example 2: strnatcmp('Price 12.09', 'Price 12.15');
    // *     returns 2: -1
    // *     example 3: strnatcmp('Price 12.90', 'Price 12.15');
    // *     returns 3: 1
    // *     example 4: strnatcmp('Version 12.9', 'Version 12.15', true);
    // *     returns 4: -6
    // *     example 5: strnatcmp('Version 12.15', 'Version 12.9', true);
    // *     returns 5: 6
    var i = 0;

    if (f_version == undefined) {
        f_version = false;
    }

    var __strnatcmp_split = function (f_string) {
        var result = [];
        var buffer = '';
        var chr = '';
        var i = 0,
            f_stringl = 0;

        var text = true;

        f_stringl = f_string.length;
        for (i = 0; i < f_stringl; i++) {
            chr = f_string.substring(i, i + 1);
            if (chr.match(/\d/)) {
                if (text) {
                    if (buffer.length > 0) {
                        result[result.length] = buffer;
                        buffer = '';
                    }

                    text = false;
                }
                buffer += chr;
            } else if ((text == false) && (chr == '.') && (i < (f_string.length - 1)) && (f_string.substring(i + 1, i + 2).match(/\d/))) {
                result[result.length] = buffer;
                buffer = '';
            } else {
                if (text == false) {
                    if (buffer.length > 0) {
                        result[result.length] = parseInt(buffer, 10);
                        buffer = '';
                    }
                    text = true;
                }
                buffer += chr;
            }
        }

        if (buffer.length > 0) {
            if (text) {
                result[result.length] = buffer;
            } else {
                result[result.length] = parseInt(buffer, 10);
            }
        }

        return result;
    };

    var array1 = __strnatcmp_split(f_string1 + '');
    var array2 = __strnatcmp_split(f_string2 + '');

    var len = array1.length;
    var text = true;

    var result = -1;
    var r = 0;

    if (len > array2.length) {
        len = array2.length;
        result = 1;
    }

    for (i = 0; i < len; i++) {
        if (isNaN(array1[i])) {
            if (isNaN(array2[i])) {
                text = true;

                if ((r = this.strcmp(array1[i], array2[i])) != 0) {
                    return r;
                }
            } else if (text) {
                return 1;
            } else {
                return -1;
            }
        } else if (isNaN(array2[i])) {
            if (text) {
                return -1;
            } else {
                return 1;
            }
        } else {
            if (text || f_version) {
                if ((r = (array1[i] - array2[i])) != 0) {
                    return r;
                }
            } else {
                if ((r = this.strcmp(array1[i].toString(), array2[i].toString())) != 0) {
                    return r;
                }
            }

            text = false;
        }
    }

    return result;
}
