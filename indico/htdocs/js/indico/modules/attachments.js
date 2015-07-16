(function(global) {
    'use strict';

    $(document).ready(function() {
        $('.attachments > .dropdown').parent().dropdown();
        setupAttachmentPreview();
    });

    global.setupAttachmentPreview = function setupAttachmentPreview() {
        var attachment = $('.js-preview-dialog');
        var pageURL = location.href.replace(/#.*$/, '');

        $(window).on('hashchange', function() {
            if (location.hash.indexOf('#preview:') != 0) {
                $('.attachment-preview-dialog').trigger('ajaxDialog:close', [true]);
            } else {
                var id = location.hash.split('#preview:')[1];
                previewAttachment(id);
            }
        }).triggerHandler('hashchange');

        attachment.on('click', function(e) {
            if (e.which != 1 || e.shiftKey) {
                // ignore middle clicks and shift-clicks - people should be able to open an attachment in a new tab/window
                return;
            }
            e.preventDefault();
            location.hash = '#preview:{0}'.format($(this).data('attachmentId'));
        });

        function previewAttachment(id) {
            var attachment = $('.attachment[data-previewable][data-attachment-id="{0}"]'.format(id));
            if (!attachment.length) {
                if (history.replaceState) {
                    history.replaceState({}, attachment.data('title'), pageURL);
                }
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
                        if (history.pushState) {
                            // push the normal url if we closed the dialog manually (i.e. not using the back button)
                            history.pushState({}, attachment.data('title'), pageURL);
                        } else {
                            location.hash = '';
                        }
                    }
                },
                onOpen: function(popup) {
                    popup.canvas.closest('.ui-dialog').prev('.ui-widget-overlay').addClass('attachment-preview-overlay');
                    popup.canvas.find('.attachment-preview-content-wrapper, .attachment-download').on('click', function() {
                        popup.canvas.trigger('ajaxDialog:close');
                    });
                    popup.canvas.find('.attachment-preview-content, .attachment-preview-top-bar').on('click', function(e) {
                        e.stopPropagation();
                    });
                    $('body').add(popup.canvas.closest('.ui-dialog')).on('keydown.attachmentPreview', function(e) {
                        if (e.which === $.ui.keyCode.ESCAPE) {
                            popup.canvas.trigger('ajaxDialog:close');
                        }
                    });
                    $('html, body').addClass('prevent-scrolling');
                }
            });
        }
    };


    global.setupAttachmentEditor = function setupAttachmentEditor() {
        var editor = $('.attachment-editor');

        function flagChanged() {
            editor.trigger('ajaxDialog:setData', [true]);
        }

        editor
            .on('click', '.tree .expandable', function(e) {
                if ($(e.target).closest('.actions').length) {
                    // ignore if it comes from inside the action panel
                    return;
                }
                $(this)
                    .toggleClass('collapsed')
                    .next('.sub-tree')
                    .find('td > div')
                        .slideToggle(150);
            })
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

    global.openAttachmentManager = function openAttachmentManager(itemLocator) {
        ajaxDialog({
            url: build_url(Indico.Urls.AttachmentManager, itemLocator),
            title: $T.gettext("Manage material"),
            confirmCloseUnsaved: false,
            hidePageHeader: true,
            onClose: function(callbackData, customData) {
                if (customData) {
                    location.reload();
                }
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
