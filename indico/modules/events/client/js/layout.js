// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  global.initMenuSortable = function initMenuSortable() {
    // ui.sender seems broken (returns null) so we keep track of the sortable who sent the item manually...
    let _sender = null;
    /*
     *.sortable('cancel') is also broken thus we need to keep track of the validity of an update manually as well.
     * See 'beforeStop' for a more detailed explanation.
     */
    let _invalidUpdate = false;

    function _canDrop(evt, ui) {
      if (_sender[0] === ui.placeholder.parent()[0]) {
        // entry moved within the same list
        return true;
      }
      if (!ui.item.hasClass('nestable')) {
        return false;
      }

      const parent = ui.placeholder.closest('.menu-entry').parent();
      // valid cross-list drag if the target list is the root one or if the target list can have nested entries
      return parent[0] === undefined || parent.hasClass('allow-nested');
    }

    // delete existing sortable before recreating them
    $('.menu-entries.ui-sortable').sortable('destroy');

    $('.menu-entries').sortable({
      handle: '.drag-handle',
      placeholder: 'menu-entry-placeholder',
      axis: 'y',
      connectWith: '.connect-menu',
      start(evt, ui) {
        _sender = $(this);
        if (ui.item.hasClass('nestable')) {
          // The list only has the placeholder and the entry being dragged. It should look like an empty list.
          if (_sender.children().not('.menu-entry-placeholder').length === 1) {
            _sender.addClass('empty');
          }
          // Show empty children list which accept children
          $('.menu-entries > .allow-nested > .menu-entry > .menu-entries.empty')
            .addClass('expand')
            .parent('.menu-entry')
            .addClass('with-children');
          ui.item
            .find('> .menu-entry > .menu-entries.empty')
            .removeClass('expand')
            .parent('.menu-entry')
            .removeClass('with-children');
        }
        ui.placeholder.height(ui.helper.outerHeight());
      },
      beforeStop(evt, ui) {
        /*
         * In the case of an invalid update we need to cancel the move. But .sortable('cancel') fails internally
         * when called from here so we keep track of whether the move is valid, check in 'update' if can update
         * and then cancel the move in 'stop' if needed.
         */
        _invalidUpdate = !_canDrop(evt, ui);
      },
      stop(evt, ui) {
        // mandatory clean-up
        $('.menu-entries').removeClass('hide-placeholder');
        if (ui.item.hasClass('nestable')) {
          $('.menu-entries > .allow-nested > .menu-entry > .menu-entries.empty')
            .removeClass('expand')
            .parent('.menu-entry')
            .removeClass('with-children');
        }

        // Check if move is valid
        if (_invalidUpdate) {
          // This can only happen if a nested user-submitted entry is dropped on an invalid target list, which
          // shouldn't happen as internal nested list are not connected with the other lists.
          $(this).sortable('cancel');
        } else if (ui.item.hasClass('nestable')) {
          // remove .empty from parent list and .nestable from parent entry
          ui.item
            .closest('.menu-entries')
            .removeClass('empty')
            .parent('.menu-entry')
            .addClass('with-children')
            .parent()
            .removeClass('nestable');

          const isRoot = ui.item.closest('.menu-entry')[0] === undefined;
          // disallow adding child elements
          if (!isRoot) {
            ui.item.removeClass('allow-nested');
          }
          // allow adding children to root entries which have a list of children
          if (isRoot && ui.item.find('> .menu-entry > .menu-entries')) {
            ui.item.addClass('allow-nested');
          }

          // add empty class to sender list of children if the last entry was moved out
          if (!_sender.children().length) {
            _sender
              .addClass('empty')
              .closest('.menu-entry')
              .parent()
              .addClass('nestable');
          }
        }
        _sender = null;
      },
      over(evt, ui) {
        // hide place-holder of list which are invalid targets
        if (!_canDrop(evt, ui)) {
          ui.placeholder.closest('.menu-entries').addClass('hide-placeholder');
        }
      },
      update(evt, ui) {
        // Prevent update from nested list which does not contain the element any more.
        if (this !== ui.item.parent()[0]) {
          return;
        }
        // Don't update an invalid move.
        if (_invalidUpdate) {
          return;
        }

        evt.stopPropagation();
        const data = {};

        const position = ui.item
          .prev()
          .children('.menu-entry')
          .data('position');
        if (position !== null) {
          data.position = position;
        }

        const parentId = ui.item.closest('.menu-entry').data('entry-id');
        if (parentId !== null) {
          data.parent_id = parentId; // snake case to follow PEP8 on the back-end
        }

        $.ajax({
          url: ui.item.children('.menu-entry').data('position-url'),
          method: 'POST',
          dataType: 'json',
          data,
          complete: IndicoUI.Dialogs.Util.progress(),
          error: handleAjaxError,
        });
      },
    });
  };

  $(document)
    .on('click', '.menu-entry > .i-label > .actions > .edit-entry', function(evt) {
      evt.preventDefault();
      evt.stopPropagation();
      ajaxDialog({
        trigger: this,
        url: $(this).data('href'),
        title: $T.gettext('Menu Entry Settings'),
        onClose(data) {
          if (data) {
            $(this.trigger)
              .closest('.menu-entry')
              .replaceWith(data.entry);
          }
        },
      });
    })
    .on('indico:confirmed', '.menu-entry .enabled, .menu-entry .not-enabled', function(evt) {
      evt.stopPropagation();
      evt.preventDefault();

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          const isEnabled = data.is_enabled;
          $this
            .toggleClass('enabled', isEnabled)
            .toggleClass('not-enabled', !isEnabled)
            .parent('.actions')
            .parent('.i-label')
            .toggleClass('striped', !isEnabled);
        },
      });
    })
    .on('indico:confirmed', '.menu-entry .default, .menu-entry .not-default', function(evt) {
      evt.stopPropagation();
      evt.preventDefault();

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          const isDefault = data.is_default;
          $('.menu-entry .default')
            .removeClass('default')
            .addClass('not-default');
          $this.toggleClass('default', isDefault).toggleClass('not-default', !isDefault);
        },
      });
    })
    .on('indico:confirmed', '.menu-entry .delete-entry', function(evt) {
      evt.preventDefault();

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          if (data) {
            $('#menu-entries > .menu-entries').replaceWith(data.menu);
            initMenuSortable();
          }
        },
      });
    });
})(window);
