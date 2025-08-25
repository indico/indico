// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global repositionTooltips */

import {$T} from 'indico/utils/i18n';

(function(global) {
  function move(array, fromIndex, toIndex) {
    array.splice(toIndex, 0, array.splice(fromIndex, 1)[0]);
    return array;
  }

  global.setupMultipleItemsWidget = function setupMultipleItemsWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        uuidField: null,
        columns: null,
        sortable: false,
        columnChoices: null,
      },
      options
    );

    const widget = $(`#${options.fieldId}-widget`);
    const widgetBody = widget.children('table').children('tbody');
    const field = $(`#${options.fieldId}`);
    const data = JSON.parse(field.val());
    const addButton = $(`#${options.fieldId}-add-button`);
    const deleteButton = $('<a>', {
      class: 'action-icon icon-remove js-remove-row',
      href: '#',
      title: $T('Delete'),
    });
    const saveButton = $('<a>', {
      class: 'action-icon icon-floppy js-save-row',
      href: '#',
      title: $T('Save'),
    });
    const editButton = $('<a>', {
      class: 'action-icon icon-edit js-edit-row',
      href: '#',
      title: $T('Edit'),
    });
    const cancelButton = $('<a>', {
      class: 'action-icon icon-close js-cancel-edit',
      href: '#',
      title: $T('Cancel'),
    });
    let initialIndex;

    if (!data.length) {
      createRow();
    }

    data.forEach(item => {
      createRow(item);
    });

    if (options.sortable) {
      fixWidths();

      widget.find('tbody').sortable({
        axis: 'y',
        containment: 'parent',
        cursor: 'move',
        distance: 10,
        handle: '.sort-handle',
        items: '> tr',
        tolerance: 'pointer',
        forceHelperSize: true,
        forcePlaceholderSize: true,
        helper(e, item) {
          const originals = item.children();
          const helper = item.clone();
          helper.children().each(function(i) {
            $(this).width(originals.eq(i).width());
          });
          return helper;
        },
        start(e, ui) {
          initialIndex = ui.item.index();
        },
        update(e, ui) {
          move(data, initialIndex, ui.item.index());
          updateField();
        },
      });
    }

    widget
      .on('click', '.js-remove-row', function(e) {
        e.preventDefault();
        removeRow($(this).closest('tr'));
      })
      .on('click', '.js-save-row', function(e) {
        e.preventDefault();
        const row = $(this).closest('tr');
        const item = {};
        let requiredFieldIsEmpty = false;
        let invalidNumber = false;
        if (options.uuidField && row.data('uuid')) {
          item[options.uuidField] = row.data('uuid');
        }
        options.columns.forEach((col, i) => {
          const inputField = row.find('.js-table-input').eq(i);
          let value = inputField.val().trim();
          if (!value && inputField.data('required')) {
            requiredFieldIsEmpty = true;
            inputField.addClass('hasError');
          } else if (inputField.attr('type') === 'checkbox') {
            item[col.id] = inputField.prop('checked');
          } else {
            item[col.id] = value;
            inputField.removeClass('hasError');
          }
          if (inputField.attr('type') === 'number' && !requiredFieldIsEmpty) {
            value = parseFloat(value);
            if (
              (inputField.attr('min') && value < parseFloat(inputField.attr('min'))) ||
              (inputField.attr('max') && value > parseFloat(inputField.attr('max')))
            ) {
              invalidNumber = true;
              inputField.addClass('hasError');
              inputField.trigger('multipleItemsWidget:showNumberError');
            } else {
              inputField.removeClass('hasError');
              inputField.trigger('multipleItemsWidget:hideNumberError');
            }
          }
        });
        if (requiredFieldIsEmpty) {
          row.trigger('multipleItemsWidget:showRequiredError');
        } else {
          row.trigger('multipleItemsWidget:hideRequiredError');
        }
        if (!requiredFieldIsEmpty && !invalidNumber) {
          if (row.data('hasItem')) {
            data[row.index()] = item;
          } else {
            data.push(item);
            row.data('hasItem', true);
          }
          updateField();
          updateRow(row, false, false);
        }
      })
      .on('click', '.js-add-row', e => {
        e.preventDefault();
        createRow();
      })
      .on('click', '.js-cancel-edit', function(e) {
        e.preventDefault();
        const row = $(this).closest('tr');
        if (!row.data('hasItem')) {
          removeRow(row);
        } else {
          updateRow(row, false, false);
        }
      })
      .on('click', '.js-edit-row', function(e) {
        e.preventDefault();
        const row = $(this).closest('tr');
        updateRow(row, true, false);
      })
      .on('keypress', 'input', function(e) {
        if (e.keyCode === 13) {
          e.preventDefault();
          $(this).closest('tr').find('.js-save-row').trigger('click');
        } else if (e.keyCode === 27) {
          e.preventDefault();
          $(this).closest('tr').find('.js-cancel-edit').trigger('click');
        }
      });

    function fixWidths() {
      if (!options.sortable) {
        return;
      }
      widget
        .find('tbody > tr > td, tbody > tr, tbody')
        .each(function() {
          // remove the fixed width to allow regular table sizing
          $(this).width('');
        })
        .each(function() {
          // fix the iwdth to avoid ugly changes during sorting
          const $this = $(this);
          $this.width($this.width());
        });
    }

    function rowsChanged(moveTooltips) {
      if (options.sortable) {
        widget.find('tbody.ui-sortable').sortable('refresh');
      }
      fixWidths();
      addButton.prop('disabled', !!widget.find('.js-table-input').length);
      if (moveTooltips === undefined || moveTooltips) {
        repositionTooltips();
      }
    }

    function makeColData(item, col, forceEditable) {
      if (item && !forceEditable) {
        if (col.type === 'select') {
          return {text: options.columnChoices[col.id][item[col.id]]};
        } else if (col.type === 'checkbox') {
          return {
            html: $('<span>', {
              class: 'icon-checkbox-{0}'.format(item[col.id] ? 'checked' : 'unchecked'),
            }),
            css: {
              'text-align': 'center',
            },
          };
        } else {
          return {text: item[col.id]};
        }
      } else if (col.type === 'select') {
        const sel = $('<select>', {
          class: 'js-table-input',
          'data-required': col.required,
        });
        sel.append($('<option>')); // Default empty option
        for (const choiceID in options.columnChoices[col.id]) {
          sel.append(
            $('<option>', {
              value: choiceID,
              text: options.columnChoices[col.id][choiceID],
              selected: item ? item[col.id] === choiceID : false,
            })
          );
        }
        return {html: sel};
      } else if (col.type === 'checkbox') {
        return {
          html: $('<input>', {
            type: 'checkbox',
            class: 'js-table-input',
            value: '1',
            checked: item ? item[col.id] : false,
          }),
        };
      } else if (col.type === 'number') {
        const numberInput = $('<input>', {
          type: 'number',
          class: 'js-table-input',
          value: item ? item[col.id] : '',
          placeholder: col.caption,
          'data-required': col.required,
          min: col.min,
          max: col.max,
          step: col.step ? col.step : 'any',
        });
        initNumberErrorMessage(numberInput, col.min, col.max);
        return {html: numberInput};
      } else if (col.type === 'textarea') {
        return {
          html: $('<textarea>', {
            class: 'js-table-input multiline',
            value: item ? item[col.id] : '',
            placeholder: col.caption,
            'data-required': col.required,
          }),
        };
      } else {
        // Assuming the type is 'text'
        return {
          html: $('<input>', {
            type: 'text',
            class: 'js-table-input',
            value: item ? item[col.id] : '',
            placeholder: col.caption,
            'data-required': col.required,
          }),
        };
      }
    }

    function initNumberErrorMessage($element, min, max) {
      $element.qtip({
        style: {
          classes: 'qtip-danger',
        },
        content: {
          text() {
            if (min && max) {
              return $T.gettext('Must be between {0} and {1}').format(min, max);
            } else if (min) {
              return $T.gettext('Must be above {0}').format(min);
            } else {
              return $T.gettext('Must be below {0}').format(max);
            }
          },
        },
        show: {
          event: 'multipleItemsWidget:showNumberError',
        },
        hide: {
          event: 'multipleItemsWidget:hideNumberError',
        },
      });
    }

    function initRequiredErrorMessage($element) {
      $element.qtip({
        style: {
          classes: 'qtip-danger',
        },
        content: {
          text: $T('Please fill in the required fields.'),
        },
        position: {
          my: 'left middle',
          at: 'right middle',
          adjust: {x: 15},
        },
        show: {
          event: 'multipleItemsWidget:showRequiredError',
        },
        hide: {
          event: 'multipleItemsWidget:hideRequiredError',
        },
      });
    }

    function createRow(item) {
      const row = $('<tr>');
      initRequiredErrorMessage(row);
      row.data('hasItem', !!item);
      if (options.uuidField && item) {
        row.data('uuid', item[options.uuidField]);
      }
      if (options.sortable) {
        $('<td>', {class: 'sort-handle'}).appendTo(row);
      }
      options.columns.forEach(col => {
        const column = $('<td>', makeColData(item, col));
        if (col.type === 'textarea') {
          column.addClass('multiline');
        }
        column.appendTo(row);
      });
      $('<td>', {
        html: item
          ? deleteButton.clone().add(editButton.clone())
          : cancelButton.clone().add(saveButton.clone()),
        class: 'js-action-col',
      }).appendTo(row);
      widgetBody.append(row);
      rowsChanged();
    }

    function updateRow(row, editMode, moveTooltips) {
      row.children('td:not(.sort-handle):not(.js-action-col)').each(function(i) {
        const column = $('<td>', makeColData(data[row.index()], options.columns[i], editMode));
        if (options.columns[i].type === 'textarea') {
          column.addClass('multiline');
        }
        $(this).replaceWith(column);
      });
      if (editMode) {
        row.children('.js-action-col').html(cancelButton.clone().add(saveButton.clone()));
      } else {
        row.children('.js-action-col').html(deleteButton.clone().add(editButton.clone()));
      }
      rowsChanged(moveTooltips);
    }

    function removeRow(row) {
      if (row.data('hasItem')) {
        data.splice(row.index(), 1);
        updateField();
      }
      row.remove();
      rowsChanged(false);
    }

    function updateField() {
      field.val(JSON.stringify(data)).trigger('change');
    }
  };
})(window);
