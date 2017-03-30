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

(function(global) {
    'use strict';

    var HISTORY_API_SUPPORTED = !!history.pushState;

    function toggleFolder(evt) {
        if ($(evt.target).closest('.actions').length) {
            // ignore if it comes from inside the action panel
            return;
        }
        $(this)
            .toggleClass('collapsed')
            .next('.sub-tree')
            .find('td > div')
                .slideToggle(150);
    }

    $(document).ready(function() {
        $('.attachments > .dropdown').parent().dropdown();
        if (!$('html').data('static-site')) {
            setupAttachmentPreview();
        }

        $(document).on('click', '[data-attachment-editor]', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            if (this.disabled || $this.hasClass('disabled')) {
                return;
            }
            var locator = $(this).data('locator');
            var title = $(this).data('title');
            var reloadOnChange = $this.data('reload-on-change') !== undefined;
            openAttachmentManager(locator, title, reloadOnChange, $this);
        });
    });

    global.setupAttachmentPreview = function setupAttachmentPreview() {
        var attachment = $('.js-preview-dialog');
        var pageURL = location.href.replace(/#.*$/, '');

        // Previewer not supported on mobile browsers
        if ($.mobileBrowser) {
            return;
        }

        $(window).on('hashchange', function(e, initial) {
            if (location.hash.indexOf('#preview:') !== 0) {
                $('.attachment-preview-dialog').trigger('ajaxDialog:close', [true]);
            } else {
                if (initial && HISTORY_API_SUPPORTED) {
                    var hash = location.hash;
                    // start with a clean state, i.e. [..., page, page+preview]
                    history.replaceState({}, document.title, pageURL);
                    history.pushState({}, document.title, location.href + hash);
                }
                var id = location.hash.split('#preview:')[1];
                previewAttachment(id);
            }
        }).triggerHandler('hashchange', [true]);

        attachment.on('click', function(e) {
            if (e.which != 1 || e.shiftKey || e.metaKey || e.ctrlKey || e.altKey) {
                // ignore middle clicks and modifier-clicks - people should be able to open
                // an attachment in a new tab/window skipping the previewer, even if they use
                // a weird mouse with less than three buttons.
                return;
            }
            e.preventDefault();
            location.hash = '#preview:{0}'.format($(this).data('attachmentId'));
        });

        function clearHash() {
            if (HISTORY_API_SUPPORTED) {
                // if we have the history api, we can assume that the previous state is the same page without
                // a preview hash (since we ensure this in the initial/fake hashchange event on page load)
                history.back();
            } else {
                // old browsers with no pushState support: the # wil stay which is a bit ugly,
                // but let's not break history (we WILL "spam" history though, but that's what you
                // get when using ancient browsers)
                location.hash = '';
            }
        }

        function previewAttachment(id) {
            var attachment = $('.attachment[data-previewable][data-attachment-id="{0}"]'.format(id));
            if (!attachment.length) {
                clearHash();
                return;
            }
            ajaxDialog({
                url: build_url(attachment.attr('href'), {preview: '1'}),
                title: attachment.data('title'),
                dialogClasses: 'attachment-preview-dialog',
                onClose: function(data) {
                    $('body').off('keydown.attachmentPreview');
                    $('html, body').removeClass('prevent-scrolling');
                    if (!data) {
                        // get rid of the hash if we closed the dialog manually (i.e. not using the back button,
                        // in which case the hash should already be gone)
                        clearHash();
                    }
                },
                onOpen: function(popup) {
                    var dialog = popup.canvas.closest('.ui-dialog');
                    dialog.prev('.ui-widget-overlay').addClass('attachment-preview-overlay');
                    popup.canvas.find('.attachment-preview-content-wrapper, .js-close-preview').on('click', function() {
                        popup.canvas.trigger('ajaxDialog:close');
                    });
                    popup.canvas.find('.attachment-download').on('click', function() {
                        var $this = $(this);
                        var href = $this.attr('href');
                        $this.attr('href', build_url(href, {from_preview: '1', download: '1'}));
                        _.defer(function() {
                            $this.attr('href', href);
                        });
                    });
                    popup.canvas.find('.attachment-preview-content, .attachment-preview-top-bar').on('click', function(e) {
                        e.stopPropagation();
                    });
                    $('body').add(dialog).on('keydown.attachmentPreview', function(e) {
                        if (e.which === $.ui.keyCode.ESCAPE) {
                            popup.canvas.trigger('ajaxDialog:close');
                        }
                    });
                    $('html, body').addClass('prevent-scrolling');
                    // for some reason the dialog is hidden when its position
                    // gets updated so we explicitly show it.
                    _.defer(function() {
                        dialog.show();
                    });
                },
                onLoadError: function(xhr) {
                    var hash = location.hash;
                    clearHash();
                    if (xhr.status == 404) {
                        alertPopup($T.gettext('This file no longer exists. Please reload the page.'));
                        return false;
                    } else if (xhr.status != 403) {
                        return;
                    }
                    if (Indico.User && Indico.User.id !== undefined) {
                        alertPopup($T('You are not authorized to access this file.'), $T('Access Denied'));
                    } else {
                        var msg = $T('This file is protected. You will be redirected to the login page.');
                        confirmPrompt(msg, $T('Access Denied')).then(function() {
                            location.href = build_url(Indico.Urls.Login, {next: location.href + hash});
                        });
                    }
                    return false;
                }
            });
        }
    };

    global.setupAttachmentTreeView = function setupAttachmentTreeView() {
        $('.attachments-box').on('click', '.tree .expandable', toggleFolder);
    };


    global.setupAttachmentEditor = function setupAttachmentEditor() {
        var editor = $('.attachment-editor');

        function flagChanged() {
            editor.trigger('ajaxDialog:setData', [true]);
        }

        editor
            .on('click', '.tree .expandable', toggleFolder)
            .on('click', '.js-dialog-action', function(e) {
                e.preventDefault();
                var $this = $(this);
                ajaxDialog({
                    trigger: this,
                    url: $this.data('href'),
                    title: $this.data('title'),
                    hidePageHeader: true,
                    onClose: function(data) {
                        if (data) {
                            $('#attachments-container').html(data.attachment_list);
                            flagChanged();
                        }
                    }
                });
            })
            .on('indico:confirmed', '.js-delete', function(e) {
                e.preventDefault();

                var $this = $(this);
                $.ajax({
                    url: $this.data('href'),
                    method: $this.data('method'),
                    complete: IndicoUI.Dialogs.Util.progress(),
                    error: handleAjaxError,
                    success: function(data) {
                        $('#attachments-container').html(data.attachment_list);
                        handleFlashes(data, true, editor);
                        flagChanged();
                    }
                });
            });
    };

    global.openAttachmentManager = function openAttachmentManager(itemLocator, title, reloadOnChange, trigger) {
        reloadOnChange = reloadOnChange === undefined ? true : reloadOnChange;
        ajaxDialog({
            trigger: trigger,
            url: build_url(Indico.Urls.AttachmentManager, itemLocator),
            title: title || $T.gettext("Manage material"),
            confirmCloseUnsaved: false,
            hidePageHeader: true,
            onClose: function(callbackData, customData) {
                if (customData && reloadOnChange) {
                    location.reload();
                } else if (customData && trigger) {
                    trigger.trigger('attachments:updated');
                }
            }
        });
    };

    global.reloadManagementAttachmentInfoColumn = function reloadManagementAttachmentInfoColumn(itemLocator, column) {
        $.ajax({
            url: build_url(Indico.Urls.ManagementAttachmentInfoColumn, itemLocator),
            method: 'GET',
            error: handleAjaxError,
            success: function(data) {
                column.replaceWith(data.html);
            }
        });
    };

    global.messageIfFolderProtected = function messageIfFolderProtected(protectionField, folderField, protectionInfo, selfProtection, inheritedProtection, folderProtection) {
        folderField.on('change', function() {
            var selectedFolder = $(this);
            if (protectionInfo[selectedFolder.val()] && !protectionField.prop('checked')) {
                selfProtection.hide();
                inheritedProtection.hide();
                folderProtection.find('.folder-name').html(selectedFolder.children('option:selected').text());
                folderProtection.show();
            }
            else {
                folderProtection.hide();
                selfProtection.toggle(protectionField.prop('checked'));
                inheritedProtection.toggle(!protectionField.prop('checked'));
            }
        });
        _.defer(function() {
            folderField.triggerHandler('change');
        });
    };

    global.setupAttachmentTooltipButtons = function setupAttachmentTooltipButtons() {
        $('.attachments-tooltip-button').each(function() {
            var button = $(this);
            button.qtip({
                content: {
                    text: button.next('.material_list')
                },
                show: {
                    event: 'click'
                },
                hide: {
                    event: 'unfocus'
                },
                position: {
                    my: 'top right',
                    at: 'bottom left'
                },
                events: {
                    show: function() {
                        button.addClass('open');
                    },
                    hide: function() {
                        button.removeClass('open');
                    }
                },
                style: {
                    classes: 'material_tip'
                }
            });
        });
    };
})(window);
