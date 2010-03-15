type("PopupDialog", ["PopupWidget"], {
    draw: function(content, x, y) {
        return this.PopupWidget.prototype.draw.call(this, content, x, y);
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

type("ExclusivePopup", ["PopupWidget", "Printable"], {

    open : function() {
        this.PopupWidget.prototype.open.call(this);
    },

    draw : function(content, customStyle) {
        var self = this;
        customStyle = any(customStyle, {});

        this.greyBg = Html.div({ className: this.printable ? 'noprint' : '',
            style: {
                'opacity': 0.5, /* Standard */
                'filter': 'alpha(opacity=50)', /* IE */
                '-khtml-opacity': 0.5, /* Older versions of Safari */
                '-moz-opacity': 0.5, /* Older versions of Mozilla */
                'background': '#444444',
                'position': 'fixed',
                'width': '100%',
                'height': '100%',
                'left': pixels(0),
                'top': pixels(0)
            }
        });
        IndicoUI.assignLayerLevel(this.greyBg);
        $E(document.body).append(this.greyBg);

        // This is the div that is being printed when user clicks print
        this.content = Html.div({}, content);

        this.contentWrapper = Html.div({style: {padding: pixels(10)}}, this.content);
        this.container = Html.div({className: 'exclusivePopup' + (this.printable ? ' noprint' : ''), style: customStyle}, this.contentWrapper);

        this.titleDiv = Html.div('title', this.title);
        this.titleWrapper = Html.div('titleWrapper', this.titleDiv);

        if (this.title && this.title !== '') {
            // A 20*20px div is added into the existing div to set the size, work-around for an IE bug
            this.container.append(Html.div('exclusivePopupTopBg', Html.div({style: {width: '20px', height: '20px'}})));
            this.container.append(this.titleWrapper);
            this.contentWrapper.setStyle('paddingTop', '0px');
        }
        this.container.append(this.contentWrapper);

        this.closeButton = null;
        if (this.closeHandler !== null) {
            this.closeButton = Html.div('exclusivePopupCloseButton');
            this.closeButton.observeClick(function(e) {
                if (self.closeHandler()) {
                    self.close();
                }
            });
            this.titleWrapper.append(this.closeButton);
        }

        this.printLink = null;
        if (this.showPrintButton) {
            this.printLink = Html.div('printLink', Html.div('printButton fakeLink', 'Print'));
            this.titleWrapper.append(this.printLink);
            this.printLink.observeClick(function() {
               self.print();
            });
        }


        return this.PopupWidget.prototype.draw.call(this, this.container, 0, 0);
    },

    close: function() {
        IndicoUI.unAssignLayerLevel(this.greyBg);
        $E(document.body).remove(this.greyBg);

        this.PopupWidget.prototype.close.call(this);
    },

    postDraw: function() {

        this.winDim = getWindowDimensions();

        this._adjustContentWrapper();
        this._postDrawPositionDialog();
        this._postDrawAdjustTitle();
    },

    _calculateContentHeight: function(){
        var winHeight = this.winDim.height - 100;
        var contentHeight = this.contentWrapper.dom.offsetHeight;

        // If content is to big for the window
        if (contentHeight > winHeight) {
            // If the window is larger than maxHeight, use the latter
            if (winHeight > this.maxHeight) {
                contentHeight = this.maxHeight;
            } else {
                // otherwise limit the content to the window height
                contentHeight = winHeight;
            }
        }
        return contentHeight;
    },

    _adjustContentWrapper: function(){
        // This is done in order to make sure that the scrollbar is shown
        // if the content is too big or if new content is added after the popup
        // dialog is displayed.
        var contentHeight = this._calculateContentHeight();
        this.contentWrapper.setStyle('height', pixels(contentHeight));
        //this.contentWrapper.setStyle('marginTop', pixels((this.closeHandler && !this.title) ? 30 : 10));
        this.contentWrapper.setStyle('marginBottom', '10px');
        this.contentWrapper.setStyle('overflowY', 'auto');
        this.contentWrapper.setStyle('overflowX', 'hidden');
        this.contentWrapper.setStyle('paddingRight', '10px');
    },

    _postDrawPositionDialog: function(){
        var left = Math.floor((this.winDim.width - this.container.dom.offsetWidth) / 2);
        var top = Math.floor((this.winDim.height - this.container.dom.offsetHeight) / 2);

        this.canvas.dom.style.left = pixels(left);
        this.canvas.dom.style.top = pixels(top);
    },

    _postDrawAdjustTitle: function() {
        // Make sure the title has correct right padding depending on close button and
        // print button;
        var titlePaddingRight = 20;
        if (this.closeButton) {
            titlePaddingRight += 30;
        }
        if (this.printLink) {
            titlePaddingRight += this.printLink.dom.offsetWidth;
        }
        this.titleDiv.dom.style.paddingRight = pixels(titlePaddingRight);
    },

    print: function() {
        if (!exists(this.printDiv)) {
            this.printDiv = Html.div({className: 'onlyPrint', style: {position: 'absolute', top: '10px', left: '10px'}});
            $E(document.body).append(this.printDiv);
        }

        this.printDiv.dom.innerHTML = this.content.dom.innerHTML;

        this.Printable.prototype.print.call(this, this.printDiv);
    }
    },
     function (title, closeButtonHandler, printable, showPrintButton) {
         this.title = any(title, null);

         // Called when user clicks the close button, if the function
         // returns true the dialog will be closed.
         this.closeHandler = any(closeButtonHandler, positive);

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

         this.PopupWidget();
    }
);

/**
 * Builds an exclusive popup with a button bar
 * Constructor arguments: the same ones as ExclusivePopup
 */
type("ExclusivePopupWithButtons", ["ExclusivePopup"], {

    /**
     * Draws the dialog
     * @param {XElement} mainContent the content that will go in the center of the popup
     * @param {XElement} buttonContent the content that will go in the button bar
     * @param {object} popupCustomStyle An object with custom styles attributes, will be passed to ExclusivePopup.draw
     * @param {object} mainContentStyle An object with custom styles attributes for the "mainContent" of the dialog,
     *                                  useful if we do not want padding:10px, for example
     * @param {object} buttonBarStyle An object with custom styles attributes for the "buttonBarStyle" of the dialog,
     *                                useful if we do not want text-align: center, for example
     */
    draw: function(mainContent, buttonContent, popupCustomStyle, mainContentStyle, buttonBarStyle) {

        popupCustomStyle = any(popupCustomStyle, {});
        if (!exists(popupCustomStyle.backgroundColor)) {
            popupCustomStyle.backgroundColor = '#F8F8F8';
        }

        mainContentStyle = any(mainContentStyle, {});
        var mainContentDiv = Html.div({className: "popupWithButtonsMainContent", style:mainContentStyle}, mainContent);

        var canvas = this.ExclusivePopup.prototype.draw.call(this, mainContentDiv, popupCustomStyle);

        buttonBarStyle = any(buttonBarStyle, {});
        var buttonDiv = Html.div({className: "popupButtonBar", style: buttonBarStyle}, buttonContent);

        this.container.append(buttonDiv);

        return canvas;

    },

    /**
     * Overloads ExclusivePopup._adjustContentWrapper
     */
    _adjustContentWrapper: function() {
        this.contentWrapper.setStyle('padding', pixels(0));
        this.contentWrapper.setStyle('overflowY', 'auto');
        this.contentWrapper.setStyle('overflowX', 'hidden');
        this.contentWrapper.setStyle('position', 'relative');
        this.contentWrapper.setStyle('top', pixels(-10));

        var contentHeight = this._calculateContentHeight();
        this.contentWrapper.setStyle('height', pixels(contentHeight));
    }
},
    function(title, closeButtonHandler, printable, showPrintButton){
        this.ExclusivePopup(title, closeButtonHandler, printable, showPrintButton);
    }
);

type("BalloonPopup", ["PopupDialog"], {
    draw: function(x, y) {
        var self = this;

        this.closeButton = Html.div({className: 'balloonPopupCloseButton'});
        this.balloonContent = Html.div({className: 'balloonPopup'}, this.closeButton, this.content);
        this.arrowDiv = Html.div({className: 'balloonPopupArrow', style: {width: this.arrowWidth, height: this.arrowHeight}});
        this.mainDiv = Html.div({}, this.balloonContent, this.arrowDiv);

        // Hide it until everything is prepared
        this.mainDiv.dom.style.visibility = 'hidden';

        // Sets the orientation to up
        this.switchOrientation();

        var toReturn = this.PopupDialog.prototype.draw.call(this, this.mainDiv, x, y);

        this.arrowDiv.dom.style.left = pixels(0);
        this.closeButton.observeClick(function() {self.close();});

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

        if ((this.y - height) < getScrollOffset().y )  {
            if ((getWindowDimensions().height + getScrollOffset().y) > (this.y + height)) {
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
        if (leftPos - getScrollOffset().x < 0) {
            leftPos = getScrollOffset().x + 5; // 5 pixel margin

            // Check if the arrow is outside the balloon, then move the balloon to
            // a correct position based on the arrow
            var arrowLeftMargin = this.x - Math.floor(this.arrowWidth/2) - this.cornerRadius;
            if (arrowLeftMargin < leftPos) {
                leftPos = arrowLeftMargin;
            }
        }
        // Check if the balloon is outside the right side of browser windows
        // Counts width 25px margin because of the scrollbar.
        else if (leftPos + balloonWidth > getScrollOffset().x + getWindowDimensions().width - 25) {

            leftPos = getScrollOffset().x + getWindowDimensions().width - balloonWidth - 25;

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
     function(content, triggerElement, closeHandler, nonCloseElements) {
         this.PopupDialog(content, triggerElement, closeHandler, nonCloseElements);

         // Constants
         this.arrowHeight = 19;
         this.arrowWidth = 35;
         this.cornerRadius = 6;
     }
);

/**
 * Utility function to display a simple alert popup.
 * You can think of it as an "alert" replacement.
 * It will have a title, a close button, and an OK button.
 * @param {Html or String} title The title of the error popup.
 * @param {Element} content Anything you want to put inside.
 */
type("AlertPopup", ["ExclusivePopup"],
    {
         draw: function() {
             var self = this;
             var okButton = Html.button({style:{marginTop: pixels(20)}}, $T('OK'));
             okButton.observeClick(function(){
                 self.close();
             });

             return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {maxWidth: pixels(400), textAlign: 'center'}}, Html.div({style: {textAlign: 'left'}}, this.content), okButton));
         }
    },

    function(title, content) {
        this.content = content;
        this.ExclusivePopup(Html.div({style:{textAlign: 'center'}},title), positive);
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
        var self = this;
        var content = this._formatContent(lines, 0);

        this.AlertPopup(Html.span('warningTitle', title), content);
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
                 errorList = Html.span({className:"errorList"}, this.errors[0]);
             }else{
                 errorList = Html.ul("errorList");
                 each(this.errors, function(e) {
                     errorList.append(Html.li('', e));
                 });
             }

             return this.ExclusivePopup.prototype.draw.call(this,
                                                            Widget.block([errorList, this.afterMessage]));
         }
     },

     function(title, errors, afterMessage) {
         this.afterMessage = afterMessage;
         this.errors = errors;
         this.ExclusivePopup(title, function() {return true;});
     }
    );
