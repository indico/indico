/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

// Global scripts that should be executed on all pages

$(document).ready(function() {
    // Create static tabs. They just load the target URL and use no ajax whatsoever
    $('.static-tabs').each(function() {
        var tabCtrl = $(this);
        tabCtrl.tabs({
            active: tabCtrl.data('active')
        });
        // Turn tabs into plain links and fix urls (needed for the active tab)
        $('> .ui-tabs-nav a', this).each(function() {
            var $this = $(this);
            tabCtrl.data('ui-tabs')._off($this, 'click');
            $this.attr('href', $this.data('href'));
        });
    });

    // Remove ui-widget-content style from static tabs as it messes up e.g. link colors
    $('.static-tabs').find('.ui-widget-content').addBack().removeClass('ui-widget-content');

    $('.main-breadcrumb a[href="#"]').css({cursor: 'default', outline: 'none'}).on('click', function(e) {
        e.preventDefault();
    });

    // Use qtip for context help

    $.fn.qtip.defaults = $.extend(true, {}, $.fn.qtip.defaults, {
        position: {
            my: 'top center',
            at: 'bottom center'
        },
        hide: {
            event: 'click mouseout'
        }
    });

    $('.contextHelp[title]').qtip();

    /* Add qTips to elements with a title attribute. The position of the qTip
     * can be specified in the data-qtip-position attribute and is one of
     * "top", "left", "bottom" or "right". It defaults to "bottom".
     *
     * It is also possible to have HTML inside the qTip by using the
     * data-qtip-html attribute instead of the title attribute. */
    $(document).on("mouseenter",
                   '[title]:not([title=""]):not(iframe), [data-qtip-html], [data-qtip-oldtitle]:not(iframe)',
                   function(event) {
        var $target = $(this),
            title = ($target.attr('title') || $target.data('qtip-oldtitle') || '').trim(),
            extraOpts = $(this).data('qtip-opts') || {},
            qtipClass = $(this).data('qtip-style'),
            qtipHTMLContainer = $(this).data('qtip-html'),
            qtipHTML = (qtipHTMLContainer && qtipHTMLContainer.length) ? $(this).next(qtipHTMLContainer) : null;

        if (!qtipHTML && !title) {
            return;
        }

        $target.attr('data-qtip-oldtitle', title);
        $target.removeAttr('title');

        var position = $(this).data('qtip-position');
        var positionOptions;
        if (position == "left") {
            positionOptions = {
                my: 'right center',
                at: 'left center'
            };
        } else if (position == "right") {
            positionOptions = {
                my: 'left center',
                at: 'right center'
            };
        } else if (position == "top") {
            positionOptions = {
                my: 'bottom center',
                at: 'top center'
            };
        }

        /* Attach the qTip to a new element to avoid side-effects on all elements with "title" attributes. */
        var container = $('<span>').qtip($.extend(true, {}, {
            overwrite: false,
            position: $.extend({
                target: $target
            }, positionOptions),

            show: {
                event: event.type,
                ready: true
            },

            content: {
                text: function() {
                    if (qtipHTML) {
                        return qtipHTML.html();
                    } else {
                        return title.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    }
                }
            },

            events: {
                show: function(event) {
                    if ($(event.originalEvent.target).hasClass('open')) {
                        event.preventDefault();
                    }
                },

                hide: function(event) {
                    $(this).qtip('destroy');
                },

                render: function(event, api) {
                    $target.on('DOMNodeRemovedFromDocument remove', function(evt) {
                        api.destroy();
                    });
                }
            },

            hide: {
                event: 'mouseleave',
                target: $target
            },

            style: {
                classes: qtipClass ? 'qtip-' + qtipClass : null
            }
        }, extraOpts), event);
    });

    // Enable colorbox for links with .js-lightbox
    $('body').on('click', 'a.js-lightbox', function() {
        $(this).colorbox({
            maxHeight: '90%',
            maxWidth: '90%',
            loop: false,
            photo: true,
            returnFocus: false
        });
    });

    $('.contextHelp[data-src]').qtip({
        content: {
            text: function() {
                return $($(this).data('src')).removeClass('tip');
            }
        }
    });

    $('.js-dropdown').each(function() {
        $(this).parent().dropdown({selector: '.js-dropdown'});
    });

    if (navigator.userAgent.match(/Trident\/7\./)) {
        // Silly IE11 will clear the second password field if
        // password autocompletion is enabled!
        // https://social.msdn.microsoft.com/Forums/en-US/7d02173f-8f45-4a74-90bf-5dfbd8f9c1de/ie-11-issue-with-two-password-input-fields
        $('input:password').each(function(){
            if (!this.value && this.getAttribute('value')) {
                this.value = this.getAttribute('value');
            }
        });
    }

    // jQuery UI prevents anything outside modal dialogs from gaining focus.
    // This breaks e.g. the session color date selector. To fix this we prevent
    // the focus trap (focusin event bound on document) from ever receiving the
    // event in case the z-index of the focused event is higher than the dialog's.
    function getMaxZ(elem) {
        var maxZ = 0;
        elem.parents().addBack().each(function() {
            var z = +$(this).css('zIndex');
            if (!isNaN(z)) {
                maxZ = Math.max(z, maxZ);
            }
        });
        return maxZ;
    }

    $('body').on('focusin', function(e) {
        if(!$.ui.dialog.overlayInstances) {
            return;
        }

        if(getMaxZ($(e.target)) > getMaxZ($('.ui-dialog:visible:last'))) {
            e.stopPropagation();
        }
    });

    // Prevent BACK in browser with backspace when focused on a readonly field
    $('input, textarea').on('keydown', function(e) {
        if (this.readOnly && e.which == K.BACKSPACE) {
            e.preventDefault();
        }
    });

    $('input.permalink').on('focus', function() {
        this.select();
    });

    showFormErrors();
});
