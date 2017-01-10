/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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


function mouseOverSwitch(observable, overAction, outAction) {

    observable.observeEvent('mouseover', function(event) {
        overAction(event);
    });

    observable.observeEvent('mouseout', function(event) {
        outAction(event);
    });

}

function highlightWithMouse(observable, target) {

    /*
     * observable - trigger element (mouse over, out)
     * target - target element (will look brighter)
     */

    if (target.__highlightSet) {
        return observable;
    }

    mouseOverSwitch(observable,
                    function() {
                        target.__tmpColor = target.dom.style.backgroundColor;
                        if (target.__tmpColor === ''){
                            return;
                        }

                        var bgColor = target.dom.style.backgroundColor;
                        var s = bgColor.match(/rgb\((\d+), (\d+), (\d+)\)/);
                        if (!s) {
                            s = bgColor.match(/#(..)(..)(..)/);
                            if (!s) {
                                return;
                            }
                            s[1] = parseInt('0x'+s[1],16);
                            s[2] = parseInt('0x'+s[2],16);
                            s[3] = parseInt('0x'+s[3],16);
                        }

                        s[1] = Math.floor(s[1]*1.05);
                        s[2] = Math.floor(s[2]*1.05);
                        s[3] = Math.floor(s[3]*1.05);
                        target.setStyle('backgroundColor', 'rgb(' + s[1] + ',' + s[2] + ',' + s[3] + ')');
                    },
                    function() {
                        target.setStyle('backgroundColor', target.__tmpColor);
                    });

    target.__highlightSet = true;

    return observable;
}

type('Printable', [], {
    print: function(element, title) {
        var body = $E(document.body);
        var bodyCSSClasses = body.dom.className;
        var elementCSSClasses = element.dom.className;

        // Make sure element is visible when printing
        element.dom.className = elementCSSClasses + " print";

        // Make sure body is invisible
        body.dom.className = bodyCSSClasses += " noprint";

        window.print();

        // Restore
        //body.dom.className = bodyCSSClasses;
        //element.dom.className = elementCSSClasses
    }
});
