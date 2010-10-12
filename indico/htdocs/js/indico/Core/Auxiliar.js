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
