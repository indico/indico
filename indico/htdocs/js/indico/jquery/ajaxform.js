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

/* global showFormErrors:false, initForms:false, confirmPrompt:false, updateHtml:false */
/* global getDropzoneFiles:false, setDropzoneFiles:false */

(function(global) {
    'use strict';

    global.inlineAjaxForm = function inlineAjaxForm(options) {
        options = $.extend(true, {
            // the element used to trigger events etc. may also be a selector.
            // when using it, the element should not be inside any element
            // that will be updated by this function as events would
            // not bubble up properly.  in many cases using the button that
            // triggers the loading of the form may be the most suitable
            // element unless it is being replaced with the form, in which case
            // its parent element may be a good candidate.
            context: null,
            // an element that triggers loading the form when clicked. if not set,
            // the form will be loaded immediately.
            trigger: null,
            // settings related to loading the form, can be set to null if the
            // form is already available on the page
            load: {
                url: null,
                method: 'GET',
                data: {}
            },
            // only applicable if the form is not loaded with ajax.  setting it
            // to true will assume that the form is not visible/editable at the
            // beginning and thus not bind e.g. the onbeforeunload event.  when
            // using this you most likely want to trigger `ajaxForm:externalShow`
            // and `ajaxForm:externalHide` on the `context` element when the form
            // becomes visible/accessible and/or hidden again
            initiallyHidden: false,
            // whether to scroll to the form after showing it
            scrollToForm: false,
            // the element whose contents will be replaced with the form after
            // loading it.  may also be a selector.
            formContainer: null,
            // selector to match elements in the form which will act as a cancel
            // button reverting the form container to its previous state
            closeSelector: '[data-button-back]',
            // ask the user to confirm closing the form (or navigating away)
            // when there are unsaved changes
            confirmCloseUnsaved: false,
            // settings on what should be updated on successful submission.
            // set to null to not update anything.
            update: {
                // the element to update with html received after successfully
                // submitting the form.  may also be a selector.
                element: null,
                // whether to replace the element itself instead of its contents
                replace: false,
                // whether to highlight the updated element for a short moment
                highlight: false
            }
        }, options);

        var formUrl = options.load ? options.load.url : location.href;
        var formContainer = $(options.formContainer);
        var formVisible = false;
        var oldContent = null;
        var savedFiles = {};
        var context = options.context ? $(options.context) : null;

        function triggerEvent(name) {
            if (!context) {
                return false;
            }
            var evt = $.Event(name);
            context.trigger(evt, [].slice.call(arguments, 1));
            return evt.isDefaultPrevented();
        }

        function updateFormUrl(xhr) {
            var loadedUrl = xhr.getResponseHeader('X-Indico-URL');
            if (loadedUrl) {
                // in case of a redirect we need to update the url used to submit
                // the ajaxified form.  otherwise url normalization might fail during
                // the POST requests.  we also remove the _=\d+ cache buster since
                // it's only relevant for the GET request and added there automatically
                formUrl = loadedUrl.replace(/&_=\d+/, '').replace(/\?_=\d+$/, '').replace(/\?_=\d+&/, '?');
            }
        }

        function loadForm() {
            $.ajax({
                url: options.load.url,
                method: options.load.method,
                data: options.load.data,
                cache: false,
                dataType: 'json',
                complete: IndicoUI.Dialogs.Util.progress(),
                error: function(xhr) {
                    if (!triggerEvent('ajaxForm:loadError', xhr)) {
                        handleAjaxError(xhr);
                    }
                },
                success: function(data, _, xhr) {
                    updateFormUrl(xhr);
                    showForm(data);
                }
            });
        }

        function showForm(data) {
            var triggerShow = false;
            if (!formVisible) {
                oldContent = formContainer.contents().detach();
                formVisible = true;
                triggerShow = true;
                if (options.confirmCloseUnsaved) {
                    $(window).on('beforeunload', onBeforeUnload);
                }
            }
            formContainer.html(data.html);
            formContainer.find(options.closeSelector).on('click', function(evt) {
                evt.preventDefault();
                var msg;
                if (options.confirmCloseUnsaved && (msg = onBeforeUnload()) !== undefined) {
                    confirmPrompt(msg, $T.gettext('Unsaved changes')).then(hideForm);
                } else {
                    hideForm();
                }
            });
            ajaxifyForms();
            if (data.js) {
                $('body').append(data.js);
            }
            if (triggerShow) {
                triggerEvent('ajaxForm:show');
                if (options.scrollToForm) {
                    $('body, html').animate({
                        scrollTop: formContainer.offset().top
                    });
                }
            }
            _.defer(function() {
                formContainer.focusFirstField();
            });
        }

        function hideForm() {
            if (options.confirmCloseUnsaved) {
                $(window).off('beforeunload', onBeforeUnload);
            }
            if (!formVisible || !options.load) {
                return;
            }
            formVisible = false;
            formContainer.html(oldContent);
            oldContent = null;
            triggerEvent('ajaxForm:hide');
        }

        function _bindEvents($form) {
            var killProgress;

            $form.on('ajaxForm:beforeSubmit', function() {
                killProgress = IndicoUI.Dialogs.Util.progress();
                // save files from dropzone fields so we can re-populate in case of failure
                $.extend(savedFiles, getDropzoneFiles($form));
            }).on('ajaxForm:error', function(evt, xhr) {
                if (killProgress) {
                    killProgress();
                }
                evt.preventDefault();
                handleAjaxError(xhr);
            }).on('ajaxForm:success', function(evt, data) {
                if (killProgress) {
                    killProgress();
                }

                if (data.success) {
                    savedFiles = {};
                    hideForm();
                    var updateOpts = options.update;
                    if (updateOpts) {
                        updateHtml(updateOpts.element, data, updateOpts.replace, updateOpts.highlight);
                    } else if (data.redirect) {
                        if (!data.redirect_no_loading) {
                            IndicoUI.Dialogs.Util.progress();
                        }
                        location.href = data.redirect;
                    }
                } else if (data.html) {
                    showForm(data);
                    // restore files in dropzone fields
                    $.each(savedFiles, function(id, files) {
                        setDropzoneFiles($('#' + id), files);
                    });
                    savedFiles = {};
                }
            });
        }

        function ajaxifyForms(noInit) {
            var forms = formContainer.find('form');
            if (!noInit) {
                showFormErrors(formContainer);
                initForms(forms);
            }
            forms.each(function() {
                var $this = $(this);
                _bindEvents($this);
                $this.ajaxForm(_getAjaxFormArgs($this));
            });
        }

        function _getAjaxFormArgs($form) {
            return {
                url: $form.attr('action') || formUrl,
                dataType: 'json',
                beforeSubmit: function() {
                    if ($form.data('dropzoneField')) {
                        // Dropzone takes care of the form submission
                        return false;
                    }
                    var evt = $.Event('ajaxForm:validateBeforeSubmit');
                    $form.trigger(evt);
                    if (evt.isDefaultPrevented()) {
                        return false;
                    }
                    $form.trigger('ajaxForm:beforeSubmit');
                },
                error: function(xhr) {
                    $form.trigger('ajaxForm:error', [xhr]);
                },
                success: function(data) {
                    $form.trigger('ajaxForm:success', [data]);
                }
            };
        }

        function hasChangedFields() {
            var forms = formContainer.find('form');
            return !!forms.length && !!forms.filter(function() {
                return $(this).data('fieldsChanged');
            }).length;
        }

        function onBeforeUnload() {
            if (hasChangedFields()) {
                return $T.gettext('You have unsaved changes that will be lost.');
            }
        }

        if (context) {
            context.on('ajaxForm:externalShow', function() {
                if (options.confirmCloseUnsaved) {
                    $(window).on('beforeunload', onBeforeUnload);
                }
            });
            context.on('ajaxForm:externalHide', function(evt, deferred) {
                var msg;
                if (!options.confirmCloseUnsaved) {
                    deferred.resolve();
                } else if ((msg = onBeforeUnload()) === undefined) {
                    deferred.resolve();
                } else {
                    confirmPrompt(msg, $T.gettext('Unsaved changes')).then(function() {
                        deferred.resolve();
                    }, function() {
                        deferred.reject();
                    });
                }
                if (options.confirmCloseUnsaved) {
                    deferred.then(function() {
                        $(window).off('beforeunload', onBeforeUnload);
                    });
                }
            });
        }

        if (!options.load) {
            // we don't go through showForm for an immediately-visible form
            if (options.confirmCloseUnsaved && !options.initiallyHidden) {
                $(window).on('beforeunload', onBeforeUnload);
            }
            ajaxifyForms(true);
        } else if (options.trigger) {
            options.trigger.on('click', function(evt) {
                evt.preventDefault();
                loadForm();
            });
        } else {
            loadForm();
        }
    };
})(window);
