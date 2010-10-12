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
        alert("You can only insert tags in Subject or Body.\nPlease click in the Subject or Body text box before inserting.");
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
        return false
        else if (currentArea.dom.id == 'notificationTplBody' || currentArea.dom.id == 'notificationTplSubject')
            return true;
        else
            return false;
}