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
    },
    /**
     * Adds an element to the list of elements that when clicked
     * on do not trigger close of the popup dialog.
     */
    addNonCloseTriggeringElement: function(element) {
        this.nonCloseTriggeringElements.push(element);
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
        var container = $('<div class="exclusivePopup"/>').css(popupStyle).append(content);

        this.showCloseButton = !!this.title;
        this._makeCanvas();
        this.canvas.empty().css(customStyle).append(container);
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
        else if(e.keyCode && e.keyCode === $.ui.keyCode.ESCAPE) {
            e.stopPropagation(); // otherwise this triggers twice for some reason
            if(this.closeHandler === null || !this.showCloseButton) {
                // Ignore escape if we don't have a close button
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
    }
}, function(title, closeButtonHandler, printable, showPrintButton, noCanvas){
    this.ExclusivePopup(title, closeButtonHandler, printable, showPrintButton, noCanvas);
});

type("BalloonPopup", ["PopupDialog"], {
    draw: function(x, y) {
        var self = this;

        this.closeButton = Html.div({className: 'balloonPopupCloseButton'});
        this.balloonContent = Html.div({className: this.balloonClass}, this.hasCloseButton ? this.closeButton : '', this.content);
        this.arrowDiv = Html.div({className: this.arrowClass, style: {width: this.arrowWidth, height: this.arrowHeight}});
        this.mainDiv = Html.div({}, this.balloonContent, this.arrowDiv);

        // Hide it until everything is prepared
        this.mainDiv.dom.style.visibility = 'hidden';

        // Sets the orientation to up
        this.switchOrientation();

        var toReturn = this.PopupDialog.prototype.draw.call(this, this.mainDiv, x, y);

        this.arrowDiv.dom.style.left = pixels(0);

        if (this.hasCloseButton) {
            this.closeButton.observeClick(function() {self.close();});
        }

        return toReturn;
    },
    open: function(x, y) {
        var self = this;

        this.x = x;
        this.y = y;

        this.PopupDialog.prototype.open.call(this, x, y);
        this.verifyXPos();
        this.verifyYPos();

        // Everything is done, can now be shown to user
        this.mainDiv.dom.style.visibility = 'visible';
    },
    switchOrientation: function() {
        if (this.balloonContent.dom.style.bottom === '') {
            // current orientation is down, set it to up
            this.balloonContent.dom.style.bottom = pixels(this.arrowHeight - 1);
            this.balloonContent.dom.style.top = '';
            this.arrowDiv.dom.style.backgroundPosition = '0 -6px';
            this.arrowDiv.dom.style.top = '';
            this.arrowDiv.dom.style.bottom = pixels(0);
        } else {
            // current orientation is up, set it to down
            this.balloonContent.dom.style.top = pixels(this.arrowHeight - 1);
            this.balloonContent.dom.style.bottom = '';
            this.arrowDiv.dom.style.backgroundPosition = '0px -25px';
            this.arrowDiv.dom.style.bottom = '';
            this.arrowDiv.dom.style.top = pixels(0);
        }
    },
    verifyYPos: function() {
        var height = this.getBalloonHeight();

        if ((this.y - height) < 5) {
            this.switchOrientation();
            return;
        }

        if ((this.y - height) < $(window).scrollTop())  {
            if (($(window).height() + $(window).scrollTop()) > (this.y + height)) {
                this.switchOrientation();
                return;
            }
        }
    },
    verifyXPos: function() {
        var balloonWidth = this.balloonContent.dom.offsetWidth;

        // Try place the middle of the balloon on mouse pointer position
        var leftPos = this.x - Math.floor(balloonWidth/2);

        // Check if the balloon is outside left side of browser window
        if (leftPos - $(window).scrollLeft() < 0) {
            leftPos = $(window).scrollLeft() + 5; // 5 pixel margin

            // Check if the arrow is outside the balloon, then move the balloon to
            // a correct position based on the arrow
            var arrowLeftMargin = this.x - Math.floor(this.arrowWidth/2) - this.cornerRadius;
            if (arrowLeftMargin < leftPos) {
                leftPos = arrowLeftMargin;
            }
        }
        // Check if the balloon is outside the right side of browser windows
        // Counts width 25px margin because of the scrollbar.
        else if (leftPos + balloonWidth > $(window).scrollLeft() + $(window).width() - 25) {

            leftPos = $(window).scrollLeft() + $(window).width() - balloonWidth - 25;

            // Check if the arrow is outside the balloon, then move the balloon to
            // a correct position based on the arrow
            var arrowRightMargin = this.x + Math.floor(this.arrowWidth/2) + this.cornerRadius;
            if (arrowRightMargin > leftPos + balloonWidth) {
                leftPos = arrowRightMargin - balloonWidth;
            }
        }

        this.canvas.dom.style.left   = pixels(leftPos);
        this.arrowDiv.dom.style.left = pixels(this.x - leftPos - Math.floor(this.arrowWidth/2));
    },
    getBalloonHeight: function() {
        return this.balloonContent.dom.offsetHeight +
            this.arrowDiv.dom.offsetHeight;
    }
    },
     function(content, triggerElement, closeHandler, nonCloseElements, balloonClass, arrowClass) {
         this.PopupDialog(content, triggerElement, closeHandler, nonCloseElements);

         this.hasCloseButton = exists(closeHandler);

         this.balloonClass = balloonClass || 'balloonPopup';
         this.arrowClass = arrowClass || 'balloonPopupArrow';

         // Constants
         this.arrowHeight = 19;
         this.arrowWidth = 35;
         this.cornerRadius = 6;
     }
);

/**
 * Utility function to display a simple notification popup.
 * @param {XElement} pointElement The element that triggers the event (onClick on it will be ignored)
 * @param {XElement} content Anything you want to put inside.
 */
type("NotificationBalloonPopup", ["BalloonPopup"],
     {
     },
     function(pointElement, content) {
         this.pointElement = pointElement;

         var canvas = Html.div({style:
                                {padding: '5px'}}, content);

         this.BalloonPopup(canvas,
                           pointElement,
                           null,
                           null,
                           'balloonPopup yellowBalloon',
                           'balloonPopupArrow yellowArrow');
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
            return this.ExclusivePopup.prototype.draw.call(this, this.content);
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

    function(title, content, handler, buttonTitle, cancelButtonTitle) {
        var self = this;

        this.buttonTitle = buttonTitle || 'OK';
        this.cancelButtonTitle = cancelButtonTitle || 'Cancel';
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
type("ConfirmPopupWithPM", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            return this.ExclusivePopup.prototype.draw.call(this, this.content);
        },
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

    function(title, content, handler) {
        var self = this;

        this.content = content;
        this.handler = handler;
        this.parameterManager = new IndicoUtil.parameterManager();
        this.ExclusivePopupWithButtons(title, function(){
            self.handler(false);
            return true;
        });
    }
);

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


/**
 * Utility function to display a three buttons popup.
 * The difference with ConfirmButton is the existence of a third button.
 * Apart from the title and close button, the three buttons display Save, Don't Save and Cancel
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 * @param {function} handler A function that will be called with an Integer as argument:
 *                   1 if the user press "Save", 2 for "Don't Save", 0 for "Cancel"
 */
type("SaveConfirmPopup", ["ExclusivePopupWithButtons"],
    {
        draw: function() {
            return this.ExclusivePopupWithButtons.prototype.draw.call(this, this.content);
        },

        _getButtons: function() {
            var self = this;
            return [
                [$T('Save'), function() {
                    self.close();
                    self.handler(1);
                }, true],
                [$T('Don\'t Save'), function() {
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

    function(title, content, handler) {
        var self = this;

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
