// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global choiceConfirmPrompt:false, confirmPrompt:false, build_url:false */

import {$T} from 'indico/utils/i18n';

(function(global) {
  // TODO: Add plugin i18n
  const $t = $T;

  global.eventManageVCRooms = function() {
    $('.js-vcroom-remove').on('click', function(e) {
      e.preventDefault();
      const $this = $(this);
      let title, msg;

      function execute(url) {
        const csrf = $('<input>', {
          type: 'hidden',
          name: 'csrf_token',
          value: $('#csrf-token').attr('content'),
        });
        $('<form>', {
          action: url,
          method: 'post',
        })
          .append(csrf)
          .appendTo('body')
          .submit();
      }

      if ($this.data('numEvents') === 1) {
        title = $t('Delete videoconference room');
        msg = `${$t('Do you really want to remove this videoconference room from the event?')} ${$t(
          'Since it is only used in this event, it will be deleted from the server, too!'
        )}`;
        msg += $this.data('extraMsg');
        confirmPrompt(msg, title).then(function() {
          execute($this.data('href'));
        });
      } else {
        title = $t('Detach videoconference room');
        msg = $t
          .ngettext(
            '*',
            'This videoconference room is used in other Indico events.<br>Do you want to \
            <strong>delete</strong> it from all {0} events or just <strong>detach</strong> \
            it from this event?',
            $this.data('numEvents')
          )
          .format($this.data('numEvents'));
        msg += $this.data('extraMsg');
        choiceConfirmPrompt(msg, title, $t('Detach'), $t('Delete')).then(function(choice) {
          const url = build_url($this.data('href'), {delete_all: choice === 2 ? '1' : ''});
          execute(url);
        });
      }
    });

    $('.js-vcroom-refresh').on('click', function(e) {
      e.preventDefault();
      const $this = $(this);
      const csrf = $('<input>', {
        type: 'hidden',
        name: 'csrf_token',
        value: $('#csrf-token').attr('content'),
      });
      $('<form>', {
        action: $this.data('href'),
        method: 'post',
      })
        .append(csrf)
        .appendTo('body')
        .submit();
    });

    $('.vc-room-entry.deleted').qtip({
      content: $T(
        'This room has been deleted and cannot be used. You can detach it from the event, however.'
      ),
      position: {
        my: 'top center',
        at: 'bottom center',
      },
    });

    $('.toggle-details')
      .on('click', function(e) {
        e.preventDefault();
        const $this = $(this);

        if ($this.closest('.vc-room-entry.deleted').length) {
          return;
        }

        $this
          .closest('tr')
          .next('tr')
          .find('.details-container')
          .slideToggle({
            start() {
              $this.toggleClass('icon-next icon-expand');
            },
          });
      })
      .filter('.vc-room-entry:not(.deleted) .toggle-details')
      .qtip({content: $T('Click to toggle collapse status')});

    $('.toggle .i-button').on('click', function() {
      const toggle = $(this);
      toggle.toggleClass('icon-eye icon-eye-blocked');
      const $input = toggle.siblings('input');
      $input.prop('type', $input.prop('type') === 'text' ? 'password' : 'text');
    });
  };
})(window);
