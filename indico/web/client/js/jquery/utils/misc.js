// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global ConfirmPopup, SpecialRemovePopup, AlertPopup, handleFlashes, cornerMessage */

import {$T} from 'indico/utils/i18n';

import Palette from '../../utils/palette';

(function(global) {
  global.confirmPrompt = function confirmPrompt(message, title) {
    const dfd = $.Deferred();
    message = $('<div>', {width: 400, text: message});
    new ConfirmPopup(title || $T('Please confirm'), message, confirmed => {
      if (confirmed) {
        dfd.resolve();
      } else {
        dfd.reject();
      }
    }).open();
    return dfd.promise();
  };

  global.choiceConfirmPrompt = function choiceConfirmPrompt(message, title, choice1, choice2) {
    const dfd = $.Deferred();
    message = $('<div>', {width: 400, html: message});
    new SpecialRemovePopup(
      title || $T('Please confirm'),
      message,
      action => {
        if (action === 0) {
          dfd.reject();
        } else {
          dfd.resolve(action);
        }
      },
      choice1,
      choice2
    ).open();
    return dfd.promise();
  };

  global.alertPopup = function alertPopup(message, title) {
    const dfd = $.Deferred();
    new AlertPopup(title, message, () => {
      dfd.resolve();
    }).open();
    return dfd;
  };

  global.handleFlashes = function handleFlashes(data, clear, element) {
    let container;
    if (!element || !element.length) {
      container = $('#flashed-messages');
    } else if (element.hasClass('flashed-messages')) {
      container = element;
    } else {
      container = element.closest('.ui-dialog-content').find('.flashed-messages');
      if (!container.length) {
        container = element.closest('.page-content').find('.flashed-messages');
      }
    }
    if (!container.length) {
      container = $('#flashed-messages');
    }
    if (clear === undefined || clear) {
      container.empty();
    }
    if (data.flashed_messages) {
      const flashed = $(data.flashed_messages.trim()).children();
      container.append(flashed);
    }
  };

  global.handleNotifications = function handleNotifications(data) {
    if (data && data.flashed_messages) {
      handleFlashes(data);
    }
    if (data && data.notifications) {
      data.notifications.forEach(notification => {
        cornerMessage({
          message: notification,
          duration: 10000,
          class: 'highlight',
          actionLabel: $T.gettext('Close'),
        });
      });
    }
  };

  global.cornerMessage = function cornerMessage(options) {
    // Create nice message in bottom right corner

    options = $.extend(
      {
        actionLabel: null, // the text of the action label
        actionCallback: null, // the callback that will be invoked
        message: '', // the message that will be displayed
        progressMessage: $T.gettext('Executing operation...'), // the message that will be displayed while executing
        // the action
        feedbackMessage: $T.gettext('Operation done!'), // the message that will be displayed once the action has
        // been successfully executed
        duration: 0, // the lifetime of the message (without being clicked, 0 = forever)
        feedbackDuration: 4000, // the lifetime of the feedback message (0 = forever)
        class: '', // a class that will be added to the message box (warning, error, success or highlight)
      },
      options
    );

    let box = null;

    function _disappear(when) {
      return setTimeout(() => {
        box.fadeOut(() => {
          box.remove();
        });
      }, when);
    }

    let container = $('#corner-message-container');
    const disappearHandler = options.duration ? _disappear(options.duration) : null;

    if (!container.length) {
      container = $('<div id="corner-message-container">').appendTo('body');
    }

    box = $('<div class="corner-message">').prependTo(container);
    $('<div class="corner-message-text">').text(options.message).appendTo(box);

    if (options.class) {
      box.addClass(options.class);
    }

    if (options.actionLabel) {
      const text = $('<a class="corner-message-action" href="#">')
        .text(options.actionLabel)
        .appendTo(box);

      text.on('click', evt => {
        evt.preventDefault();

        if (disappearHandler) {
          clearTimeout(disappearHandler);
        }
        if (options.actionCallback) {
          const promise = options.actionCallback() || $.Deferred();

          box.addClass('progress').find('.corner-message-text').text(options.progressMessage);
          text.remove();

          promise
            .then(
              () => {
                box.find('.corner-message-text').text(options.feedbackMessage);
                box.removeClass(options.class).addClass('success').removeClass('progress');
              },
              () => {
                box.text($T.gettext('Operation failed!'));
                box.removeClass('progress success warning highlight').addClass('error');
              }
            )
            .always(() => {
              if (options.feedbackDuration) {
                _disappear(options.feedbackDuration);
              }
            });
        } else {
          _disappear(0);
        }
      });
    }
  };

  global.uniqueId = function uniqueId() {
    return `${Math.round(new Date().getTime() + Math.random() * 100)}`;
  };

  global.countWords = function countWords(value) {
    value = value.trim();
    return value ? value.split(/\s+/).length : 0;
  };

  function _doUpdateHtml(target, html, replace, highlight) {
    let $target = $(target);
    if (replace) {
      const $html = $($.parseHTML(html, document, true));
      $target.replaceWith($html);
      $target = $html;
    } else {
      $target.html($.parseHTML(html, document, true));
    }
    $target.trigger('indico:htmlUpdated');
    if (highlight) {
      $target.effect('highlight', {color: Palette.highlight});
    }
  }

  global.updateHtml = function updateHtml(target, data, replace, highlight) {
    if ($.isPlainObject(target)) {
      for (const key in target) {
        if (!(key in data)) {
          console.error(`Invalid key: ${key}`); // eslint-disable-line no-console
        } else {
          _doUpdateHtml(target[key], data[key], replace, highlight);
        }
      }
    } else {
      _doUpdateHtml(target, data.html, replace, highlight);
    }
  };
})(window);
