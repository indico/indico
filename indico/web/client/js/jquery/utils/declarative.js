// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable max-len */
/* global inlineAjaxForm, updateHtml, confirmPrompt, ajaxDialog, handleFlashes, handleAjaxError,
          build_url */

import {$T} from '../../utils/i18n';

(function(global) {
  $(document).ready(() => {
    setupActionLinks();
    setupAjaxForms();
    setupConfirmPopup();
    setupMathJax();
    setupSelectAllNone();
    setupAnchorLinks();
    setupToggleLinks();
  });

  function getParamsFromSelectors(selector) {
    const fieldParams = {};
    if ($.isPlainObject(selector)) {
      Object.entries(selector).forEach(([key, value]) => {
        fieldParams[key] = $(value).val();
      });
    } else {
      $(selector).each(function() {
        if (!(this.name in fieldParams)) {
          fieldParams[this.name] = [];
        }
        fieldParams[this.name].push($(this).val());
      });
    }
    return fieldParams;
  }

  global.getFormParams = function getFormParams($form) {
    return getParamsFromSelectors(
      $form.find(
        'input[type=text]:not(:disabled), input[type=time]:not(:disabled), \
                                                  input[type=number]:not(:disabled), input[type=hidden]:not(:disabled), \
                                                  input:checked:not(:disabled), textarea:not(:disabled), \
                                                  select:not(:disabled)'
      )
    );
  };

  function setupSelectAllNone() {
    $('body').on('click', '[data-select-all]', function() {
      const selector = $(this).data('select-all');
      $(selector).filter(':not(:checked)').prop('checked', true).trigger('change');
    });

    $('body').on('click', '[data-select-none]', function() {
      const selector = $(this).data('select-none');
      $(selector).filter(':checked').prop('checked', false).trigger('change');
    });
  }

  function setupConfirmPopup() {
    $('body').on(
      'click',
      '[data-confirm]:not(button[data-href]):not(input:button[data-href]):not(a[data-method][data-href]):not(a[data-ajax-dialog][data-href])',
      function() {
        const $this = $(this);

        function performAction() {
          const evt = $.Event('indico:confirmed');
          $this.trigger(evt);

          // Handle custom code
          if (evt.isDefaultPrevented()) {
            return;
          }

          if ($this.is('form')) {
            $this.submit();
          } else {
            window.location = $this.attr('href');
          }
        }

        const evtBefore = $.Event('indico:beforeConfirmed');
        $this.trigger(evtBefore);

        if (evtBefore.isDefaultPrevented()) {
          performAction();
        } else {
          confirmPrompt($(this).data('confirm'), $(this).data('title')).then(performAction);
        }

        return false;
      }
    );
  }

  function setupActionLinks() {
    const selectors = [
      'button[data-href][data-method]',
      'input:button[data-href][data-method]',
      'a[data-href][data-method]',
      'button[data-href][data-ajax-dialog]',
      'input:button[data-href][data-ajax-dialog]',
      'a[data-href][data-ajax-dialog]',
      'button[data-content][data-ajax-dialog]',
      'input:button[data-content][data-ajax-dialog]',
      'a[data-content][data-ajax-dialog]',
      'button[data-callback]',
      'input:button[data-callback]',
      'a[data-callback]',
    ];
    $('body').on('click', selectors.join(', '), function(e) {
      e.preventDefault();
      const $this = $(this);
      if ($this.hasClass('disabled')) {
        return;
      }
      const url = $this.data('href');
      const callback = $this.data('callback');
      const method = ($this.data('method') || 'GET').toUpperCase();
      let params = $this.data('params') || {};
      const paramsSelector = $this.data('params-selector');
      const update = $this.data('update');
      const ajax = $this.data('ajax') !== undefined;
      const replaceUpdate = $this.data('replace-update') !== undefined;
      const highlightUpdate = $this.data('highlight-update') !== undefined;
      const dialog = $this.data('ajax-dialog') !== undefined;
      const reload = $this.data('reload-after');
      const redirect = $this.data('redirect-after');
      const content = $this.data('content');

      if (!$.isPlainObject(params)) {
        throw new Error('Invalid params. Must be valid JSON if set.');
      }

      if (paramsSelector) {
        params = $.extend({}, getParamsFromSelectors(paramsSelector), params);
      }

      function execute() {
        const evt = $.Event('indico:confirmed');
        $this.trigger(evt);

        // Handle custom code
        if (evt.isDefaultPrevented()) {
          return;
        }

        // Handle AJAX dialog
        if (dialog) {
          const closeButton = $this.data('close-button');
          let title = $this.data('title');
          if (!title && title !== undefined) {
            // if `data-title` is present without a value, fall back to the title attr
            title = $this.attr('title') || $this.data('qtip-oldtitle');
          }
          ajaxDialog({
            trigger: $this,
            url,
            method,
            data: params,
            content: $(content).html(),
            title,
            subtitle: $this.data('subtitle'),
            closeButton: closeButton === undefined ? false : closeButton || true,
            dialogClasses: $this.data('dialog-classes'),
            hidePageHeader: $this.data('hide-page-header') !== undefined,
            confirmCloseUnsaved: $this.data('confirm-close-unsaved') !== undefined,
            onOpen: ({dialogElement}) => {
              dialogElement.trigger('indico:dialogOpen');
            },
            onClose(data, customData) {
              if (data) {
                handleFlashes(data, true, $this);
                if (update) {
                  updateHtml(update, data, replaceUpdate, highlightUpdate);
                } else if (reload !== undefined && reload !== 'customData') {
                  IndicoUI.Dialogs.Util.progress();
                  location.reload();
                } else if (redirect !== undefined) {
                  IndicoUI.Dialogs.Util.progress();
                  location.href = redirect;
                }
              } else if (reload === 'customData' && customData) {
                IndicoUI.Dialogs.Util.progress();
                location.reload();
              }
            },
          });
          return;
        }

        // Handle html update or reload
        if (ajax || update || reload !== undefined || redirect !== undefined) {
          $.ajax({
            method,
            url,
            data: params,
            error: handleAjaxError,
            complete: IndicoUI.Dialogs.Util.progress(),
            success(data) {
              const successEvt = $.Event('declarative:success');
              $this.trigger(successEvt, [data]);
              if (successEvt.isDefaultPrevented()) {
                return;
              }
              if (update) {
                handleFlashes(data, true, $this);
                updateHtml(update, data, replaceUpdate, highlightUpdate);
              } else if (reload !== undefined) {
                IndicoUI.Dialogs.Util.progress();
                location.reload();
              } else if (redirect !== undefined) {
                IndicoUI.Dialogs.Util.progress();
                location.href = redirect;
              } else if (data.redirect) {
                if (!data.redirect_no_loading) {
                  IndicoUI.Dialogs.Util.progress();
                }
                location.href = data.redirect;
              }
            },
          });
          return;
        }

        if (callback) {
          window[callback](params);
          return;
        }

        // Handle normal GET/POST
        if (method === 'GET') {
          location.href = build_url(url, params);
        } else if (method === 'POST') {
          const form = $('<form>', {
            action: url,
            method,
          });
          form.append(
            $('<input>', {
              type: 'hidden',
              name: 'csrf_token',
              value: $('#csrf-token').attr('content'),
            })
          );
          $.each(params, (key, value) => {
            form.append($('<input>', {type: 'hidden', name: key, value}));
          });
          form.appendTo('body').submit();
        }
      }

      const promptMsg = $this.data('confirm');
      let confirmed;
      if (!promptMsg) {
        confirmed = $.Deferred().resolve();
      } else {
        confirmed = confirmPrompt(promptMsg, $(this).data('title') || $T('Confirm action'));
      }
      confirmed.then(execute);
    });
  }

  function setupAjaxForms() {
    function _getOptions($elem, extra) {
      const updateOpts = $elem.data('update');
      return $.extend(
        {
          context: $elem,
          formContainer: $elem.data('form-container'),
          confirmCloseUnsaved: $elem.data('confirm-close-unsaved') !== undefined,
          update: updateOpts
            ? {
                element: $elem.data('update'),
                replace: $elem.data('replace-update') !== undefined,
                highlight: $elem.data('highlight-update') !== undefined,
              }
            : null,
        },
        extra
      );
    }

    function _handleClick(evt) {
      evt.preventDefault();
      const $this = $(this);
      if ($this.hasClass('disabled')) {
        return;
      }

      inlineAjaxForm(
        _getOptions($this, {
          load: {
            url: $this.data('href'),
          },
          scrollToForm: $this.data('scroll-to-form') !== undefined,
        })
      );

      function toggleDisabled(disabled) {
        if ($this.data('hide-trigger') !== undefined) {
          $this.toggle(!disabled);
        }
        if ($this.is('a')) {
          $this.toggleClass('disabled', disabled);
        } else {
          $this.prop('disabled', disabled);
        }

        if (disabled) {
          $this.trigger('indico:closeAutoTooltip');
        }
      }

      $this
        .on('ajaxForm:show', () => {
          toggleDisabled(true);
        })
        .on('ajaxForm:hide', () => {
          toggleDisabled(false);
        });
    }

    function _handleHtmlUpdate($elem) {
      $elem.find('form[data-ajax-form]').each(function() {
        const $this = $(this);
        inlineAjaxForm(
          _getOptions($this, {
            load: null,
            initiallyHidden: $this.data('initially-hidden') !== undefined,
          })
        );
      });
    }

    $('body').on('click', 'button[data-ajax-form], a[data-ajax-form]', _handleClick);
    $('body').on('indico:htmlUpdated', evt => {
      _handleHtmlUpdate($(evt.target));
    });
    _handleHtmlUpdate($('body'));
  }

  function setupMathJax() {
    const $elems = $('.js-mathjax');
    if ($elems.length) {
      $elems.mathJax();
    }
  }

  function setupAnchorLinks() {
    $('[data-anchor], [data-permalink]').each(function() {
      const $elem = $(this);
      const fragment = $elem.data('anchor');
      const permalink = $elem.data('permalink');
      const stripArg = $elem.data('anchor-strip-arg');

      // remove the field `stripArg` from the query string
      const params = new URLSearchParams(window.location.search);
      if (stripArg) {
        params.delete(stripArg);
      }
      const newQueryString = params.toString();
      const url = window.location.pathname + (newQueryString ? `?${newQueryString}` : '');

      $('<a>', {
        class: 'anchor-link icon-link',
        href: permalink || `${url}#${fragment}`,
        title: $elem.data('anchor-text') || $T.gettext('Direct link to this item'),
      }).appendTo($elem);
    });
  }

  function setupToggleLinks() {
    $('body').on('click', '[data-toggle]:not([data-toggle=dropdown])', function(evt) {
      evt.preventDefault();
      const $elem = $(this);
      const accordion = $elem.data('accordion');
      const toggleClass = $elem.data('toggle-class');
      const isVisible = $elem.hasClass('js-details-visible');

      function toggleDetails($trigger) {
        const $target = $($trigger.data('toggle'));
        const wasVisible = $trigger.hasClass('js-details-visible');
        $target.slideToggle('fast');
        $trigger.toggleClass('js-details-visible');
        if (toggleClass) {
          $(toggleClass.target).toggleClass(toggleClass.class);
        }
        $trigger.text(wasVisible ? $trigger.data('show-text') : $trigger.data('hide-text'));
      }

      if (!isVisible && accordion !== undefined) {
        $(accordion)
          .find('.js-details-visible')
          .each(function() {
            toggleDetails($(this));
          });
      }

      toggleDetails($elem);
    });
  }
})(window);
