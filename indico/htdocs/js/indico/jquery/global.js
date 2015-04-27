/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
        var extraOpts = $(this).data('qtipOpts') || {};
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
            onHide: function() {
                // If the parent element is destroyed we need to destroy the qTip too
                $(this).qtip('destroy');
            }
        }, extraOpts), event);
    });

    // Enable colorbox for links with rel="lightbox"
    $('body').on('click', 'a[nofollow="lightbox"]', function() {
        $(this).colorbox({
            maxHeight: '90%',
            maxWidth: '90%',
            loop: false,
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

    $('.body').on('click', '[data-confirm]:not(button[data-href])', function() {
        var $this = $(this);
        new ConfirmPopup($(this).data("title"), $(this).data("confirm"), function(confirmed){
            if (confirmed){
                if ($this.is('form')) {
                    $this.submit();
                } else {
                    window.location = self.getAttribute("href");
                }
            }
        }).open();
        return false;
    });

    $('.body').on('click', 'button[data-method][data-href]', function() {
        var $this = $(this);
        var url = $this.data('href');
        var method = $this.data('method').toUpperCase();
        var params = $this.data('params') || {};
        if (!$.isPlainObject(params)) {
            throw new Error('Invalid params. Must be valid JSON if set.');
        }

        function execute() {
            if (method == 'GET') {
                location.href = build_url(url, params);
            } else {
                var form = $('<form>', {
                    action: url,
                    method: method
                });
                $.each(params, function(key, value) {
                    form.append($('<input>', {type: 'hidden', name: key, value: value}));
                });
                form.appendTo('body').submit();
            }
        }

        var promptMsg = $this.data('confirm');
        if (promptMsg) {
            new ConfirmPopup($(this).data('title') || $T('Confirm action'), promptMsg, function(confirmed) {
                if (confirmed) {
                    execute();
                }
            }).open();
        } else {
            execute();
        }
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

    showFormErrors();
});
