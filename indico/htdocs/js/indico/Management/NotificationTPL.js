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

var currentArea;
var inputCursor = 0;

function selected(id) {
    currentArea = $E(id);
    // Get cursor position for IE
    if (currentArea.dom.id == 'notificationTplSubject' && document.selection) {
        inputCursor = getInputPosition();
    }
}

function insertTag(tag) {
    if (checkID()) {
        var value = currentArea.dom.value;
        var countChars = getCursorPosition();
        var cursor = countChars[0];
        var posToMove = countChars[1];
        var end = currentArea.dom.value.length;
        value = value.substr(0,cursor) + tag + value.substr(cursor, end);
        currentArea.dom.value = value;
        // Set the cursor below the inserted tag for IE
        if (document.selection) {
            setCursorPosition(posToMove);
        } else {
            // Set cursor position for Firefox
            currentArea.dom.selectionStart = cursor+tag.length;
            currentArea.dom.selectionEnd = cursor+tag.length;
            currentArea.dom.focus();
        }
    } else {
        new AlertPopup($T("Warning"), $T("You can only insert tags in Subject or Body.\nPlease click in the Subject or Body text box before inserting.")).open();
    }
}

function getCursorPosition() {
    // Initialize
    var cursor = 0;
    var charsAfter = 0;
    // IE Support
    if (document.selection) {
        if (currentArea.dom.id == 'notificationTplBody') {
            // Set focus on the element
            currentArea.dom.focus();
            // To get cursor position, get empty selection range
            var oSel = document.selection.createRange();
            var oSelDup = document.selection.createRange();
            // Counter for special characters
            var counter = -2;
            var previousLength = 0;
            var nextLength = 0;
            // Move selection start to 0 position
            while (oSel.text == oSel.htmlText) {
                previousLength = oSel.text.length;
                oSel.moveStart('character', -1);
                nextLength = oSel.text.length;
                // Look for newline characters
                if (previousLength == nextLength)
                    // A special character has been found
                    counter += 2;
            }

            cursor = oSel.text.length + counter;

            // Move selection end to end position
            counter = -1;
            while (oSelDup.text == oSelDup.htmlText) {
                previousLength = oSelDup.text.length;
                oSelDup.moveEnd('character', 1);
                nextLength = oSelDup.text.length;
                // Look for newline characters
                if (previousLength == nextLength)
                    // A special character has been found
                    counter += 1;
            }
            charsAfter = oSelDup.text.length - counter;
        } else { // for the input field
            cursor = inputCursor;
            charsAfter = currentArea.dom.value.length - cursor;
        }

    }
    // FF
    else if (currentArea.dom.selectionStart >= 0) {
        cursor = currentArea.dom.selectionEnd;
        charsAfter = 0;
    }

    return [cursor, charsAfter];
}

function setCursorPosition(pos) {
    if (currentArea.dom.id == 'notificationTplBody') {
        // Set focus on the element
        currentArea.dom.focus();
        var oSel = document.selection.createRange();
        // Move selection start and end to desired position
        if (pos > 0) {
            oSel.moveStart ('character', -pos);
            oSel.moveEnd ('character', -pos);
        }
        oSel.select ();
    }
}

function getInputPosition () {
    currentArea.dom.focus ();
    var oSel = document.selection.createRange ();
    oSel.moveStart ('character', -currentArea.dom.value.length);
    return oSel.text.length;
}

function checkID() {
    if (currentArea == null)
        return false;
    return currentArea.dom.id == 'notificationTplBody' || currentArea.dom.id == 'notificationTplSubject';
}


//Manager to add/modify notificaton templates
type("NotificationTemplateManager", [],
        {
            // Add elements to the PM
            addToPM: function(elem, type, allowEmpty) {
                this.__parameterManager.add(elem, type, allowEmpty);
            },

			// Check if there are some erros in the fields of the form
			checkFields: function() {
			    // Make sure that both functions are executed
                var checkPM = this.__parameterManager.check();

                if (checkPM) {
                    this.errorElement.dom.style.display = 'none';
                    return true;
                } else {
                    this.errorElement.dom.style.display = '';
                    return false;
                }
             },

             removeCheckBoxError: function() {
                 if (this.cbParent.dom.className.slice(-7) == "invalid") {
                     this.cbParent.dom.className = "";
                 }
             },

             // Check the condition of the select in the 3rd step
             checkSelectCondition: function(mainSelect, elem1, elem2) {
                 if (mainSelect.dom.value != 'accepted') {
                     elem1.dom.style.display = 'none';
                     elem2.dom.style.display = 'none';
                 } else {
                     elem1.dom.style.display = '';
                     elem2.dom.style.display = '';
                 }
             }
        },


        /* Manage the
        @param cbParent: parent of the checkboxes element
        @return the manager class for the ConfModCFANotifTplNew.tpl and ConfModCFANotifTplEditData
        */
		function(cbParent, errorElement) {
            this.__parameterManager = new IndicoUtil.parameterManager();
            this.cbParent = cbParent;
            this.errorElement = errorElement;
		});
