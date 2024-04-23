// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './ind_combobox.scss';

let lastId = 1;

function setNativeInputValue(input, value) {
  // React adds its own setter to the input and messes with the native event mechanism.
  // In order for the value to be set in a standard way, we need to resort to this hack.
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(input, value);
}

customElements.define(
  'ind-combobox',
  class IndCombobox extends HTMLElement {
    #comboId;

    constructor() {
      super();
      this.#comboId = `x-combobox-${lastId++}`;
    }

    get value() {
      return this.querySelector('input').value;
    }

    connectedCallback() {
      const listbox = this.querySelector('[role=listbox]');
      const input = this.querySelector('input');

      // Copy the input's own label as the label of the completion list.
      // This label is only spoken out when user uses the cursor key to
      // select candidates.
      const inputLabel = input.labels?.[0]?.textContent.trim();
      if (inputLabel) {
        listbox.setAttribute('aria-label', inputLabel);
      }

      // Prepare the element state

      listbox.id = `${this.#comboId}-list`;
      input.setAttribute('aria-haspopup', true);
      input.setAttribute('aria-controls', listbox.id);
      input.setAttribute('aria-autocomplete', 'both');

      // Since the end goal is to enter one of the provided items, we do not
      // expect spelling to be an issue. We also do not want the screen reader
      // announcing spelling errors for autocompleted text, as that would be
      // silly.
      input.setAttribute('spellcheck', false);

      // Each option is given a unique id so that aria-activedescendant can
      // point to them when they are selected using arrow keys.
      for (let i = 0, option; (option = listbox.children[i]); i++) {
        option.id = `${this.#comboId}-option-${i + 1}`;
        if (option.dataset.value === input.value) {
          selectOption(option);
        }
      }

      // Event handlers

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
        const option = evt.target.closest('[role=option]:not([aria-selected=true])');
        if (option) {
          selectOption(option);
          dispatchInternalInputEvent();
        }
      });

      input.addEventListener('blur', closeListbox);

      // Perform the inline autocomplete
      input.addEventListener('input', evt => {
        const value = input.value;
        const charactersWereAdded = !evt.inputType.startsWith('delete');
        let autocompleteAlreadySet = false;
        let numOptions = 0;

        deselectCurrentSelection();

        for (const option of listbox.children) {
          const optionValue = option.dataset.value;
          const hasMatch = optionValue.toLowerCase().startsWith(value.toLowerCase());

          // Filter out options that did not match the value
          option.hidden = value && !hasMatch;
          numOptions += !option.hidden;

          // If no option has been selected yet, select an option that matches
          // the filter keyword. We only do this if characters were added
          // because otherwise it would be impossible to delete characters.
          if (charactersWereAdded && !autocompleteAlreadySet && hasMatch) {
            selectOption(option);
            moveVirtualCursorToOption();
            // Select the portion of the input text that is ahead of the user-inputted filter keyword
            // (this presents the type-ahead autocomplete)
            selectInputText(value.length);
            autocompleteAlreadySet = true;
          }
        }

        toggleListbox(numOptions > 0);
      });

      // Keyboard actions
      input.addEventListener('keydown', ev => {
        switch (ev.code) {
          // Use arrow keys to navigate the options. Selection wraps.
          // When Alt key is held down, the listbox opens, but selection
          // does not change.
          case 'ArrowDown':
            ev.preventDefault();
            toggleListbox(true);
            if (ev.altKey) {
              break;
            }
            selectOptionViaKeyboard(findNextSelectableOption());
            dispatchInternalInputEvent();
            break;
          case 'ArrowUp':
            ev.preventDefault();
            toggleListbox(true);
            if (ev.altKey) {
              break;
            }
            selectOptionViaKeyboard(findPreviousSelectableOption());
            dispatchInternalInputEvent();
            break;

          // Use Enter or Escape to close
          case 'Enter':
            // Conditionally return so that Enter has the default behavior
            // when listbox is already closed.
            if (input.getAttribute('aria-expanded') !== 'true') {
              return;
            }
            ev.preventDefault();
            closeListbox();
            break;

          case 'Escape':
            ev.preventDefault();
            closeListbox();
            break;
        }
      });

      // Functions

      function dispatchInternalInputEvent() {
        input.dispatchEvent(new Event('change', {bubbles: true}));
      }

      function toggleListbox(isOpen) {
        // The list box visibility is controlled using CSS based on aria-expanded on the input
        input.setAttribute('aria-expanded', isOpen);
        listbox.querySelector('[aria-selected=true]')?.scrollIntoView({block: 'nearest'});
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

      function selectOption(option) {
        // Omit the option to clear the selection and reset the input
        deselectCurrentSelection();
        option?.setAttribute('aria-selected', true);
        setNativeInputValue(input, option?.dataset.value);
      }

      function moveVirtualCursorToOption(option) {
        // Omit the $option to remove selection
        input.setAttribute('aria-activedescendant', option?.id || '');
      }

      function selectInputText(startIndex = input.value.length) {
        input.setSelectionRange(startIndex, input.value.length);
      }

      function findNextSelectableOption() {
        const currentOption = listbox.querySelector('[aria-selected=true]');
        let nextOption = currentOption?.nextElementSibling;
        while (nextOption?.hidden) {
          nextOption = nextOption.nextElementSibling;
        }
        return nextOption || listbox.querySelector('[role=option]:not([hidden])');
      }

      function findPreviousSelectableOption() {
        const currentOption = listbox.querySelector('[aria-selected=true]');
        let previousOption = currentOption?.previousElementSibling;
        while (previousOption?.hidden) {
          previousOption = previousOption.previousElementSibling;
        }
        return (
          previousOption ||
          listbox.querySelector('[role=option]:nth-last-child(1 of :not([hidden]))')
        );
      }
    }
  }
);
