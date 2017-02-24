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

type("PopupDialog", ["PopupWidget"], {
    draw: function(content, x, y) {
        return this.PopupWidget.prototype.draw.call(this, content, x, y, null, true);
    },

    clickTriggersClosing: function(target) {
        // Check if one of the elements that should not trigger
        // close is clicked
        var nonCloseTriggeringClick = false;
        each(this.nonCloseTriggeringElements, function(e) {
            if (e.ancestorOf(target)) {
                nonCloseTriggeringClick = true;
            }
        });
        return (!this.canvas.ancestorOf(target) &&
                !this.triggerElement.ancestorOf(target) &&
                !nonCloseTriggeringClick);
    },

    open: function(x, y) {
        var self = this;
        this.PopupWidget.prototype.open.call(this, x, y);

        self.clickHandler = function(event) {
            if (self.clickTriggersClosing($E(eventTarget(event)))) {
                self.close();
            }
        };
        IndicoUtil.onclickHandlerAdd(self.clickHandler);
    },

    close: function() {
        if (this.closeHandler() && this.isopen) {
            IndicoUtil.onclickHandlerRemove(this.clickHandler);
            this.PopupWidget.prototype.close.call(this);
        }
    }
    },
     function(content, triggerElement, closeHandler, nonCloseTriggeringElements) {
         this.content = content;
         this.PopupWidget();
         this.triggerElement = triggerElement;
         this.closeHandler = any(closeHandler, function() {return true; });
         this.nonCloseTriggeringElements = any(nonCloseTriggeringElements, []);
     }
    );


type("ExclusivePopup", ["Printable"], {
    open: function() {
        this.draw();
        this.canvas.dialog('open');
    },

    draw: function(content, customStyle, popupStyle) {
        customStyle = customStyle || {};
        if(!content) {
            content = '';
        }
        else if(content.dom) {
            // support indico XElement objects
            content = content.dom;
        }

        if(popupStyle === undefined) {
            popupStyle = customStyle;
        }
        this.contentContainer = $('<div class="exclusivePopup"/>').css(popupStyle).append(content);

        this.showCloseButton = !!this.title;
        this._makeCanvas();
        this.canvas.empty().css(customStyle).append(this.contentContainer);
        this.dialogElement.css(customStyle);
    },

    close: function() {
        if(this.isopen) {
            this.canvas.dialog('close');
        }
    },

    _getDialogOptions: function() {
        return {};
    },

    _makeCanvas: function() {
        if(!this.canvas) {
            var opts = $.extend(true, {
                autoOpen: false,
                draggable: true,
                modal: true,
                resizable: false,
                closeOnEscape: true,
                title: this.title,
                minWidth: '250px',
                minHeight: 0,
                open: $.proxy(this._onOpen, this),
                close: $.proxy(this._onClose, this),
                beforeClose: $.proxy(this._onBeforeClose, this)
            }, this._getDialogOptions());
            this.canvas = $('<div/>').dialog(opts);
        }
        if(!this.dialogElement) {
            this.dialogElement = this.canvas.dialog('widget');
        }
        this.buttons = this.dialogElement.find('.ui-dialog-buttonset button');
    },

    _onBeforeClose: function(e) {
        // Close button clicked
        if(e.originalEvent && $(e.originalEvent.currentTarget).hasClass('ui-dialog-titlebar-close')) {
            if(isFunction(this.closeHandler) && !this.closeHandler()) {
                return false;
            }
        }
        // Escape key
        else if(e.originalEvent && e.originalEvent.keyCode === $.ui.keyCode.ESCAPE) {
            e.stopPropagation(); // otherwise this triggers twice for some reason
            if(this.closeHandler === null || !this.showCloseButton) {
                // Ignore escape if we don't have a close button
                // But trigger data-button-back in ajaxDialog
                this.canvas.find('[data-button-back]').trigger('click');
                return false;
            }
            if(isFunction(this.closeHandler) && !this.closeHandler()) {
                return false;
            }
        }
    },

    _onOpen: function(e) {
        this.isopen = true;
        if(this.closeHandler === null || !this.showCloseButton) {
            this.dialogElement.find('.ui-dialog-titlebar-close').hide();
            if(!this.title) {
                this.dialogElement.find('.ui-dialog-titlebar').hide();
            }
        }

        if(this.postDraw() === true) {
            // refresh position
            var pos = this.canvas.dialog('option', 'position');
            this.canvas.dialog('option', 'position', pos);
        }
    },

    postDraw: function() {

    },

    _onClose: function(e, ui) {
        this.isopen = false;
        this.canvas.dialog('destroy');
        this.canvas.remove();
        this.canvas = this.dialogElement = null;
        this.buttons = [];
    }

}, function(title, closeButtonHandler, printable, showPrintButton, noCanvas) {
    this.title = any(title, null);

    // Called when user clicks the close button, if the function
    // returns true the dialog will be closed.
    this.closeHandler = any(closeButtonHandler, positive);
    // the close button will be enabled in draw() so if that method is overridden it will not be drawn
    this.showCloseButton = false;

    // The maximum allowed height, used since it doesn't look
    // very nice it the dialog gets too big.
    this.maxHeight = 600;

    // Decides whether the popup should be printable. That is, when the user
    // clicks print only the content of the dialog will be printed not the
    // whole page. Should be true in general unless the dialog is containing
    // something users normally don't want to print, i.e. the loading dialog.
    this.printable = any(printable, true);

    // Whether to show the print button or not in the title
    // Note: the button will only be shown if the popup dialog has a title.
    // and is printable.
    this.showPrintButton = any(showPrintButton && title && printable, false);

    this.buttons = $();
    if(!noCanvas) {
        this._makeCanvas();
    }
});




/**
 * Builds an exclusive popup with a button bar
 * Constructor arguments: the same ones as ExclusivePopup
 */
type("ExclusivePopupWithButtons", ["ExclusivePopup"], {
    _getButtons: function() {
        return null;
    },
    _getDialogOptions: function() {
        var self = this;
        var buttons = this._getButtons();
        var dlgButtons = [];
        this.defaultButton = null;
        if(buttons) {
            $.each(buttons, function(i, button) {
                dlgButtons.push({
                    text: button[0],
                    click: button[1]
                });
                if(button.length > 2 && button[2]) {
                    self.defaultButton = i;
                }
            });
        }
        return {
            buttons: dlgButtons
        };
    },
    _onOpen: function(e) {
        this.ExclusivePopup.prototype._onOpen.call(this, e);
        if(this.defaultButton !== null) {
            this.buttons[this.defaultButton].focus();
        }

        this.canvas.scrollblocker({
            overflowType: "auto"
        });
    },
    _onClose: function(e) {
        this.ExclusivePopup.prototype._onClose.call(this, e);
        $("body").off("mousewheel wheel");
    }

}, function(title, closeButtonHandler, printable, showPrintButton, noCanvas){
    this.ExclusivePopup(title, closeButtonHandler, printable, showPrintButton, noCanvas);
});


/**
 * Utility function to display a simple alert popup.
 * You can think of it as an "alert" replacement.
 * It will have a title, a close button, and an OK button.
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 */
type("AlertPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            var content = $('<div/>').css({
                maxWidth: '400px',
                padding: '10px',
                textAlign: 'center'
            }).append($('<div/>').css('textAlign', 'left').html(this.content));
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, content);
        },

        _getButtons: function() {
            var self = this;
            return [
                [$T('OK'), function() {
                    self.close();
                    self.callback();
                }]
            ];
        }
    },

    function(title, content, callback) {
        if(content.dom) {
            // Indico XElement object
            content = content.dom;
        }
        this.content = content;
        this.callback = callback || positive;
        this.ExclusivePopupWithButtons(title, this.callback);
    }
);

/**
 * Utility function to display a simple alert popup.
 * You can think of it as an "confirm" replacement.
 * It will have a title, a close button, an OK button and a Cancel button.
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 * @param {function} handler A function that will be called with a boolean as argument:
 *                   true if the user pressers "ok", or false if the user presses "cancel"
 */
type("ConfirmPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            return this.ExclusivePopup.prototype.draw.call(this, this.content, this.style);
        },
        _getButtons: function() {
            var self = this;
            return [
                [$T(this.buttonTitle), function() {
                    self.close();
                    self.handler(true);
                }],
                [$T(this.cancelButtonTitle), function() {
                    self.close();
                    self.handler(false);
                }]
            ];
        }
    },

    function(title, content, handler, buttonTitle, cancelButtonTitle, style) {
        var self = this;

        this.buttonTitle = buttonTitle || 'OK';
        this.cancelButtonTitle = cancelButtonTitle || 'Cancel';
        this.style = style || {};
        this.content = content;
        this.handler = handler;
        this.ExclusivePopupWithButtons(title, function() {
            self.handler(false);
            return true;
        });
    }
);


/**
 * Works exactly the same as the ConfirmPopup, but includes a parametermanager to perform checks when pressing OK
 */
type("ConfirmPopupWithPM", ["ConfirmPopup"],
    {
        _getButtons: function() {
            var self = this;
            return [
                [$T(this.buttonTitle), function() {
                     if(self.parameterManager.check()) {
                         self.handler(true);
                     }
                }],
                [$T(this.cancelButtonTitle), function() {
                    self.close();
                    self.handler(false);
                }]
            ];
        }
    },

    function(title, content, handler, buttonTitle, cancelButtonTitle) {
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ConfirmPopup(title, content, handler, buttonTitle, cancelButtonTitle);
    }
);

type('ConfirmPopupWithReason', ['ConfirmPopupWithPM'], {

}, function(title, content, handler, buttonTitle, cancelButtonTitle) {

    this.reason = Html.textarea({style:{width:'100%'}});

    this.ConfirmPopupWithPM(title, Html.div({}, content, Html.div({style: {marginTop:pixels(10)}},Html.div({style:{fontWeight:"bold"}}, $T("Reason: ")),this.reason)), handler, buttonTitle, cancelButtonTitle);
    this.parameterManager.add(this.reason, 'text', false);
});

/**
 * Utility function to display a three buttons popup.
 * The difference with ConfirmButton is the existence of a third button.
 * Apart from the title and close button, the three buttons display, two of them configurables and Cancel
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 * @param {function} handler A function that will be called with an Integer as argument:
 *                   1 if the user press button1, 2 for button2, 0 for "Cancel"
 */
type("SpecialRemovePopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.content);
        },

        _getButtons: function() {
            var self = this;
            return [
                [$T(this.buttonTitle1), function() {
                    self.close();
                    self.handler(1);
                }],
                [$T(this.buttonTitle2), function() {
                    self.close();
                    self.handler(2);
                }],
                [$T('Cancel'), function() {
                    self.close();
                    self.handler(0);
                }]
            ];
        }
    },

    function(title, content, handler, buttonTitle1, buttonTitle2) {
        var self = this;

        this.buttonTitle1 = buttonTitle1;
        this.buttonTitle2 = buttonTitle2;
        this.content = content;
        this.handler = handler;
        this.ExclusivePopupWithButtons(title, function(){
            self.handler(0);
            return true;
        });
    }
);


type("WarningPopup", ["AlertPopup"],
    {
        _formatLine: function(line) {
            var result = Html.div({paddingBottom: pixels(2)});


            var linkStart = 0;
            var linkMiddle;
            var linkEnd = 0;

            while (linkStart >= 0) {
                linkStart = line.indexOf('[[', linkEnd);

                if (linkStart >= 0) {
                    result.append(Html.span('',line.substring(linkEnd, linkStart)));

                    linkMiddle = line.indexOf(' ', linkStart);
                    linkEnd = line.indexOf(']]', linkStart);

                    result.append(Html.a({href: line.substring(linkStart+2, linkMiddle)}, line.substring(linkMiddle + 1, linkEnd) ));
                    linkEnd+= 2;
                } else {
                    result.append(Html.span('',line.substring(linkEnd, line.length)));
                }
            }

            return result;
        },

        _formatContent: function(content, level) {
            var self = this;

            if (isString(content)) {
                return Html.span('', self._formatLine(content));

            } else if (isArray(content)) {
                var result = Html.ul(level === 0 ? 'warningLevel0' : 'warningLevel1');
                each (content, function(line){
                    if (isString(line)) {
                        result.append(Html.li({}, self._formatLine(line)));
                    } else if (isArray(line)) {
                        result.append(self._formatContent(line, level + 1));
                    } else {
                        result.append(Html.li({}, line));
                    }
                });
                return result;
            }
        }
    },
    function(title, lines) {
        this.AlertPopup(title, this._formatContent(lines, 0).dom);
    }
);

/**
 * Utility function to display a popup with errors.
 * Useful for notifying the user of input mistakes or other errors.
 * @param {Html or String} title The title of the error popup.
 * @param {Array of String} errors An Array of strings with the errors to display.
 * @param {Html or String} afterMessage A message to display after the list of errors.
 */
type("ErrorPopup", ["ExclusivePopup"],
     {
         draw: function() {
             var errorList = null;
             if (this.errors.length == 1) {
                 errorList = Html.div({className:"errorList"}, this.errors[0]);
             }else{
                 errorList = Html.ul("errorList");
                 each(this.errors, function(e) {
                     errorList.append(Html.li('', e));
                 });
             }

             return this.ExclusivePopup.prototype.draw.call(this, Widget.block([errorList, this.afterMessage]).dom);
         }
     },

     function(title, errors, afterMessage) {
         this.afterMessage = afterMessage;
         this.errors = errors;
         this.ExclusivePopup(title, positive);
     }
    );
