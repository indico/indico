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

    $(document).on("mouseenter", '[title]:not([title=""]):not(iframe)', function(event) {
        if (!$(this).attr('title').trim()) {
            return;
        }

        var extraOpts = $(this).data('qtipOpts') || {},
            qtipClass = $(this).data('qtip-style');

        $(this).qtip($.extend(true, {}, {
            overwrite: false,
            show: {
                event: event.type,
                ready: true
            },

            content: {
                text: function() {
                    var html = $(this).attr('title') || $(this).attr('alt');
                    return html ? html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : '';
                }
            },

            events: {
                show: function(event) {
                    if ($(event.originalEvent.target).hasClass('open')) {
                        event.preventDefault();
                    }
                }
            },
            hide: {
                event: "mouseleave"
            },

            style: {
                classes: qtipClass ? 'qtip-' + qtipClass : null
            },

            onHide: function() {
                // If the parent element is destroyed we need to destroy the qTip too
                $(this).qtip('destroy');
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
        this.id = this.id || uniqueId();
        $(this).parent().dropdown({selector: '#' + this.id});
    });

    $('body').on('click', '[data-confirm]:not(button[data-href]):not(input:button[data-href]):not(a[data-method][data-href])', function() {
        var $this = $(this);
        new ConfirmPopup($(this).data("title"), $(this).data("confirm"), function(confirmed){
            if (confirmed){
                if ($this.is('form')) {
                    $this.submit();
                } else {
                    window.location = $this.attr('href');
                }
            }
        }).open();
        return false;
    });

    $('body').on('click', 'button[data-method][data-href], input:button[data-method][data-href], a[data-method][data-href]', function(e) {
        e.preventDefault();
        var $this = $(this);
        var url = $this.data('href');
        var method = $this.data('method').toUpperCase();
        var params = $this.data('params') || {};
        var update = $this.data('update');
        if (!$.isPlainObject(params)) {
            throw new Error('Invalid params. Must be valid JSON if set.');
        }

        function execute() {
            var evt = $.Event('indico:confirmed');
            $this.trigger(evt);

            // Handle custom code
            if (evt.isDefaultPrevented()) {
                return;
            }

            // Handle html update
            if (update) {
                $.ajax({
                    method: method,
                    url: url,
                    data: params,
                    error: handleAjaxError,
                    complete: IndicoUI.Dialogs.Util.progress(),
                    success: function(data) {
                        $(update).html(data.html);
                    }
                });
                return;
            }

            // Handle normal GET/POST
            if (method === 'GET') {
                location.href = build_url(url, params);
            } else if (method === 'POST') {
                var form = $('<form>', {
                    action: url,
                    method: method
                });
                form.append($('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')}));
                $.each(params, function(key, value) {
                    form.append($('<input>', {type: 'hidden', name: key, value: value}));
                });
                form.appendTo('body').submit();
            }
        }

        var promptMsg = $this.data('confirm');
        var confirmed;
        if (!promptMsg) {
            confirmed = $.Deferred().resolve();
        } else {
            confirmed = confirmPrompt(promptMsg, $(this).data('title') || $T('Confirm action'));
        }
        confirmed.then(execute);
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

    $('input, textarea').placeholder();

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
