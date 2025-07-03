// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import * as positioning from 'indico/utils/positioning';
import {Time} from 'indico/utils/time_value';

import './ind_time_picker.scss';

CustomElementBase.defineWhenDomReady(
  'ind-time-picker',
  class extends CustomElementBase {
    static lastId = 1;

    static attributes = {
      value: class InputValueProxy extends CustomElementBase.CustomAttribute {
        setValue(newValue) {
          CustomElementBase.setValue(this.elemenet.querySelector('input'), newValue);
        }

        getValue() {
          return this.element.querySelector('input').value;
        }
      },
    };

    setup() {
      const id = `combo-box-${this.constructor.lastId++}`;
      const indTimePicker = this;
      const listbox = this.querySelector('[role=listbox]');
      const input = this.querySelector('input');
      const clearButton = this.querySelector('button[value=clear]');

      // Copy the input's own label as the label of the completion list.
      // This label is only spoken out when user uses the cursor key to
      // select candidates.
      const inputLabel = input.labels?.[0]?.textContent.trim();
      if (inputLabel) {
        listbox.setAttribute('aria-label', inputLabel);
      }

      // Prepare the element state

      listbox.id = `${id}-list`;
      input.setAttribute('aria-haspopup', true);
      input.setAttribute('aria-controls', listbox.id);
      this.toggleAttribute('clearable', clearButton);
      CustomElementBase.setValue(input, this.getAttribute('value'));

      // We don't care about spelling. We're only working with times.
      input.setAttribute('spellcheck', false);

      CustomElementBase.setValue(input, this.getAttribute('value'));

      // Each option is given a unique id so that aria-activedescendant can
      // point to them when they are selected using arrow keys.
      for (let i = 0, option; (option = listbox.children[i]); i++) {
        option.id = `${id}-option-${i + 1}`;
        if (!option.dataset.value) {
          option.dataset.value = option.textContent;
        }
        if (option.dataset.value === input.value) {
          selectOption(option);
        }
      }

      toggleClearButton();

      // Event handlers

      indTimePicker.addEventListener('x-attrchange.value', () => {
        CustomElementBase.setValue(input, this.getAttribute('value'));
      });

      input.addEventListener('click', () => {
        // When user clicks the input while no candidates are matching the value,
        // ensure that all options are visible
        if (!listbox.querySelector('[role=option]:not([hidden])')) {
          for (const option of listbox.children) {
            option.hidden = false;
          }
        }
        toggleListbox(true);
      });

      listbox.addEventListener('pointerdown', evt => {
        // We use pointerdown instead of click here, because click fires after blur (see below)
        const option = evt.target.closest(
          '[role=option]:not([aria-selected=true]):not([aria-disabled])'
        );
        if (option) {
          selectOption(option);
          toggleClearButton(true);
        }
      });

      input.addEventListener('blur', closeListbox);

      // Perform time matching
      input.addEventListener(
        'input',
        evt => {
          evt.stopPropagation(); // Prevent React from messing up the standard input operation. Use native change event instead!
          deselectCurrentSelection();

          const filterKeyword = input.value.trim().toLocaleLowerCase();
          const filterTime = Time.fromString(filterKeyword).toString();
          let numMatched = 0;
          let exactMatch;

          if (filterKeyword) {
            for (const option of listbox.children) {
              const optionDisabled = option.hasAttribute('aria-disabled');
              const optionText = option.textContent.toLowerCase();
              const optionTime = option.dataset.time;

              const isMatch =
                !optionDisabled &&
                (optionText.startsWith(filterKeyword) || filterTime === optionTime);

              numMatched += isMatch;
              exactMatch ||= filterTime === optionTime && option;
            }
          }

          if (exactMatch) {
            markSelection(exactMatch);
            moveVirtualCursorToOption(exactMatch);
          }

          dispatchExternalChangeEvent();
          toggleListbox(filterKeyword && numMatched);
          toggleClearButton();
        },
        {capture: true}
      );

      // Keyboard actions
      input.addEventListener('keydown', ev => {
        switch (ev.code) {
          // Use arrow keys to navigate the options. Selection wraps.
          // When Alt key is held down, the listbox opens, but selection
          // does not change.
          case 'ArrowDown': {
            ev.preventDefault();
            toggleListbox(true);
            if (ev.altKey) {
              break;
            }
            selectOptionViaKeyboard(findNextSelectableOption());
            toggleClearButton(true);
            break;
          }
          case 'ArrowUp': {
            ev.preventDefault();
            toggleListbox(true);
            if (ev.altKey) {
              break;
            }
            selectOptionViaKeyboard(findPreviousSelectableOption());
            toggleClearButton(true);
            break;
          }
          // Use Enter or Escape to close
          case 'Enter': {
            // Conditionally return so that Enter has the default behavior
            // when listbox is already closed.
            if (input.getAttribute('aria-expanded') !== 'true') {
              return;
            }
            ev.preventDefault();
            const marked = findMarkedOption();
            if (marked) {
              selectOptionViaKeyboard(marked);
            }
            closeListbox();
            break;
          }
          case 'Escape': {
            ev.preventDefault();
            closeListbox();
            break;
          }
        }
      });

      clearButton?.addEventListener('click', () => {
        CustomElementBase.setValue(input, '');
        input.dispatchEvent(new Event('input'));
      });

      // Functions

      function toggleClearButton(show = !!input.value) {
        if (!clearButton) {
          return;
        }
        clearButton.hidden = !show;
        if (!show) {
          input.focus();
        }
      }

      function dispatchExternalChangeEvent() {
        indTimePicker.dispatchEvent(new Event('change', {bubbles: true}));
      }

      let abortPositioning;

      function toggleListbox(isOpen) {
        // The list box visibility is controlled using CSS based on aria-expanded on the input
        if (isOpen) {
          input.setAttribute('aria-expanded', true);
          listbox.hidden = false;
          abortPositioning = positioning.position(
            listbox,
            input,
            positioning.dropdownPositionStrategy,
            () => indTimePicker.toggleAttribute('open', true)
          );
          listbox.querySelector('[aria-selected=true]')?.scrollIntoView({block: 'nearest'});
        } else {
          abortPositioning?.();
          input.removeAttribute('aria-expanded');
          listbox.hidden = true;
          indTimePicker.removeAttribute('open');
        }
      }

      function closeListbox() {
        toggleListbox(false);
        selectInputText();
        // Clear the filtering
        for (const option of listbox.querySelectorAll('[hidden]')) {
          option.hidden = false;
        }
      }

      function selectOptionViaKeyboard(option) {
        selectOption(option);
        moveVirtualCursorToOption(option);
        selectInputText();
      }

      function deselectCurrentSelection() {
        listbox.querySelector('[aria-selected=true]')?.removeAttribute('aria-selected');
      }

      function markSelection(option) {
        deselectCurrentSelection();
        option?.setAttribute('aria-selected', true);
      }

      function findMarkedOption() {
        return listbox.querySelector('[aria-selected=true]');
      }

      function selectOption(option) {
        // Omit the option to clear the selection and reset the input
        markSelection(option);
        CustomElementBase.setValue(input, option?.dataset.value);
        dispatchExternalChangeEvent();
      }

      function moveVirtualCursorToOption(option) {
        // Omit the option to remove selection
        input.setAttribute('aria-activedescendant', option?.id || '');
        option?.scrollIntoView({block: 'nearest'});
      }

      function selectInputText(startIndex = input.value.length) {
        input.setSelectionRange(startIndex, input.value.length);
      }

      function findNextSelectableOption() {
        const currentOption = listbox.querySelector('[aria-selected=true]');
        let nextOption = currentOption?.nextElementSibling;
        while (nextOption?.hidden || nextOption?.hasAttribute('aria-disabled')) {
          nextOption = nextOption.nextElementSibling;
        }
        return (
          nextOption || listbox.querySelector('[role=option]:not([hidden]):not([aria-disabled])')
        );
      }

      function findPreviousSelectableOption() {
        const currentOption = listbox.querySelector('[aria-selected=true]');
        let previousOption = currentOption?.previousElementSibling;
        while (previousOption?.hidden || previousOption?.hasAttribute('aria-disabled')) {
          previousOption = previousOption.previousElementSibling;
        }
        return (
          previousOption ||
          listbox.querySelector(
            '[role=option]:nth-last-child(1 of :not([hidden]):not([aria-disabled]))'
          )
        );
      }
    }
  }
);
