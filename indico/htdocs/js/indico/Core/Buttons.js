/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
     @namespace Generic icons/buttons that are used all throughout
    *           the interface
    */
IndicoUI.Buttons = {

    /**
        * Returns an image with an 'add' icon
        */
    addButton: function(faded){
        var caption = faded ? 'Add (blocked)' : 'Add';
        return Html.img({
            alt: caption,
            title: caption,
            src: faded ? imageSrc("add_faded") : imageSrc("add"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    },
    /**
        * Returns an image with an 'remove' icon
        */
    removeButton: function(faded, fadedCaption){
        var caption = faded ? (exists(fadedCaption)? fadedCaption : 'Remove (blocked)') : 'Remove';
        return Html.img({
            alt: caption,
            title: caption,
            src: faded ? imageSrc("remove_faded") : imageSrc("remove"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    },
    /**
        * Returns an image with an 'edit' icon
        */
    editButton: function(faded, fadedCaption){
        var caption = faded ? (exists(fadedCaption) ? fadedCaption: 'Edit (blocked)') : 'Edit';
        return Html.img({

            alt: caption,
            title: caption,
            src: faded ? imageSrc("edit_faded") : imageSrc("edit"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    },

    starButton: function(faded){
        return Html.img({
            src: faded ? imageSrc("starGrey") : imageSrc("star"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    },

    /**
        * Hides/displays a target element, toggling an arrow-like "expand" icon
        * @param {XElement} target the target element, that will be hidden/shown
        * @param {Boolean} [state] The initial state of the icon
        * (true - expanded, false - collapsed [default])
        */
    arrowExpandIcon: function(target, state){
        return IndicoUI.Buttons.expandIcon(target, state,
                                           Html.img({
                                               alt: 'Collapse',
                                               src: imageSrc("itemExploded")
                                           }),
                                           Html.img({
                                               alt: 'Expand',
                                               src: imageSrc("currentMenuItem")
                                           })
                                          );
    },

    expandIcon: function(target, state /* = false */, expandedIcon, collapsedIcon, inline /* = false */){
        var img;
        var eSrc = expandedIcon.dom.src;
        var cSrc = collapsedIcon.dom.src;
        var eAlt = expandedIcon.dom.alt;
        var cAlt = collapsedIcon.dom.alt;

        if (!exists(state)) {
            state = false;
        }

        if (state) {
            img = expandedIcon;
            target.dom.style.display = inline?'inline':'block';
        } else {
            img = collapsedIcon;
            target.dom.style.display = 'none';
        }

        var elem = Widget.link(command(function(){
            if (!elem.state) {
                IndicoUI.Effect.appear(target, inline?'inline':'block');
                img.dom.src = eSrc;
                img.dom.alt = eAlt;
            } else {
                IndicoUI.Effect.disappear(target);
                img.dom.src = cSrc;
                img.dom.alt = cAlt;
            }

            elem.state = !elem.state;
            return false;
        }, img));

        elem.state = state;

        return elem;
    },

    /**
     * Creates a button with 2 different states.
     * Each state has an associated icon and an associated function.
     * Also, an object can be passed that will be passed as argument to those functions.
     * @param {Boolean} state The initial state. false = state 1, true = state 2
     * @param {XElement} icon1 An img element (typically constructed with Html.img() ). It should have at least a src and an alt attributes.
     *                         It will be displayed when state = false
     * @param {XElement} icon2 An img element (typically constructed with Html.img() ). It should have at least a src and an alt attributes.
     *                         It will be displayed when state = true
     * @param {object} associatedObject An object that will be passed as argument to function1 and function2 when they will be called.
     * @param {function} function1 A function that will be called when state is true. The object "associatedObject" will be passed to it.
     * @param {function} function2 A function that will be called when state is false. The object "associatedObject" will be passed to it.
     */
    customImgSwitchButton: function(state /* = false */, icon1, icon2, associatedObject, function1, function2) {
        var img;
        var src1 = icon1.dom.src;
        var src2 = icon2.dom.src;
        var alt1 = icon1.dom.alt;
        var alt2 = icon2.dom.alt;

        if (!exists(state)) {
            state = false;
        }
        if (!exists(function2)) {
            function2 = function1;
        }

        if (state) {
            img = icon1;
        } else {
            img = icon2;
        }

        var elem = Widget.link(command(function(){
            if (elem.state) {
                if (elem.associatedObject === null) {
                    function1();
                } else {
                    function1(elem.associatedObject);
                }
                img.dom.src = src2;
                img.dom.alt = alt2;
            } else {
                if (elem.associatedObject === null) {
                    function2();
                } else {
                    function2(elem.associatedObject);
                }
                img.dom.src = src1;
                img.dom.alt = alt1;
            }

            elem.state = !elem.state;
            return false;
        }, img));

        elem.state = state;
        elem.associatedObject = associatedObject;

        return elem;
    },
    /**
     * Creates a button with 2 different states.
     * Each state has an associated text and an associated function.
     * Also, an object can be passed that will be passed as argument to those functions.
     * @param {Boolean} state The initial state. false = state 1, true = state 2
     * @param {XElement} text1 A string. It will be displayed when state = false
     * @param {XElement} text2 A string. It will be displayed when state = true
     * @param {object} associatedObject An object that will be passed as argument to function1 and function2 when they will be called.
     * @param {function} function1 A function that will be called when state is true. The object "associatedObject" will be passed to it.
     * @param {function} function2 A function that will be called when state is false. The object "associatedObject" will be passed to it.
     */
    customTextSwitchButton: function(state /* = false */, text1, text2, associatedObject, function1, function2) {

        if (!exists(state)) {
            state = false;
        }
        if (!exists(function2)) {
            function2 = function1;
        }

        var button = Html.input('button', {});
        if (state) {
            button.set(text1);
        } else {
            button.set(text2);
        }

        var elem = Widget.link(command(function(){
            if (elem.state) {
                if (elem.associatedObject === null) {
                    function1();
                } else {
                    function1(elem.associatedObject);
                }
                button.set(text2);
            } else {
                if (elem.associatedObject === null) {
                    function2();
                } else {
                    function2(elem.associatedObject);
                }
                button.set(text1);
            }

            elem.state = !elem.state;
            return false;
        }, button));

        elem.state = state;
        elem.associatedObject = associatedObject;

        return elem;
    },

    /**
        * Returns a "SHow/Hide Advanced Options" text button that
        * switches stated when clicked
        * @param {Boolean} val 'true' for "show" and 'false' for "hide"
        * @return The link DOM Element
        */
    tabExpandButton: function(val){
        // val - if true, show the "expand" option, else show "hide"

        var showTabs = function(){
            var tabs = document.getElementById('tabList').childNodes;
            for (var i in tabs) {
                var tab = tabs[i];
                if (tab.tagName == 'LI') {
                    if (contains(tab.className, 'hiddenTab')) {
                        tab.style.display = 'inline';
                    }
                }
            }
        };

        var hideTabs = function() {
            var tabs = document.getElementById('tabList').childNodes;
            for (var i in tabs) {
                var tab = tabs[i];
                if (tab.tagName == 'LI' && contains(tab.className, 'hiddenTab')) {
                    tab.style.display = 'none';
                }
            }
        };

        var option = new Chooser({
            showLink: command(function(){
                IndicoUI.Widgets.Options.setAdvancedOptions(true, function(){
                    showTabs();
                    option.set('hideLink');
                });
            }, 'Show Advanced Options'),
            hideLink: command(function(){
                IndicoUI.Widgets.Options.setAdvancedOptions(false, function(){
                    hideTabs();
                    option.set('showLink');
                });
            }, 'Hide Advanced Options')
        });

        if (!val) {
            showTabs();
            option.set('hideLink');
        }
        else {
            option.set('showLink');
        }

        return Widget.link(option);
    }
};
