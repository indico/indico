// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import CustomElementBase from 'indico/custom_elements/_base';
import * as positioning from 'indico/utils/positioning';

import './ind_combobox.scss';

customElements.define(
  'ind-combo-box',
  class extends CustomElementBase {
    static lastId = 1;

    get value() {
      return this.querySelector('input').value;
    }

    setup() {
      const indComboBox = this;
      const id = `combo-box-${this.constructor.lastId++}`;
      const listbox = this.querySelector('[role=listbox]');
      const input = this.querySelector('input');
      const clearButton = this.querySelector('button[value=clear]');

      // Copy the input's own label as the label of the completion list.
      // This label is only spoken out when user uses the cursor key to
      // select candidates
      const inputLabel = input.labels?.[0]?.textContent.trim();
      if (inputLabel) {
        listbox.setAttribute('aria-label', inputLabel);
      }

      // Prepare the element state

      listbox.id = `${id}-list`;
      input.setAttribute('aria-haspopup', true);
      input.setAttribute('aria-controls', listbox.id);
      this.toggleAttribute('clearable', clearButton);

      // Since the end goal is to enter one of the provided items, we do not
      // expect spelling to be an issue. We also do not want the screen reader
      // announcing spelling errors for autocompleted text, as that would be
      // silly.
      input.setAttribute('spellcheck', false);

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
          dispatchInternalInputEvent();
        }
      });

      input.addEventListener('blur', closeListbox);

      // Perform the inline autocomplete/search
      input.addEventListener('input', evt => {
        deselectCurrentSelection();

        const useAutocomplete = input.getAttribute('aria-autocomplete') === 'both';
        const charactersWereAdded = !evt.inputType?.startsWith('delete'); // Manually triggered events don't have `evt.inputType`.
        const filterKeyword = input.value;
        const filterKeywordLC = filterKeyword.toLowerCase();
        let topAutocompleteRankScore = 0;
        let topAutocompleteCandidate;
        let candidateCount = 0;

        // Filter the candidates
        for (const option of listbox.children) {
          const optionValue = option.dataset.value;
          const optionValueLC = optionValue.toLowerCase();

          // We use the autocomplete candidate rank to determine the most
          // likely candidate. The most likely candidate will be inserted
          // into the input as an autocomplete candiate when autocomplete
          // is enabled. The rank does not affect sorting. A candidate with
          // the autocomplete ranking of 0 is taken out of the list of
          // suggestions.
          let autocompleteCandiateRanking = 0;

          // Skip if no filter keyword
          if (filterKeyword && !option.hasAttribute('aria-disabled')) {
            // Exact initial match
            autocompleteCandiateRanking += optionValue.startsWith(filterKeyword) * 1000;
            // Case-insensitive initial match
            autocompleteCandiateRanking += optionValueLC.startsWith(filterKeywordLC) * 100;
            if (!useAutocomplete) {
              // Case-insensitive match anywhere in the string
              autocompleteCandiateRanking += optionValueLC.includes(filterKeywordLC);
              // Exact match anywhere in the string
              autocompleteCandiateRanking += optionValue.includes(filterKeyword) * 10;
            }
          }

          option.hidden = filterKeyword && !autocompleteCandiateRanking;
          if (!option.hidden) {
            candidateCount++;
          }

          if (autocompleteCandiateRanking > topAutocompleteRankScore) {
            topAutocompleteRankScore = autocompleteCandiateRanking;
            topAutocompleteCandidate = option;
          }
        }

        const shouldAutocomplete =
          useAutocomplete && charactersWereAdded && topAutocompleteCandidate;
        if (shouldAutocomplete) {
          selectOption(topAutocompleteCandidate);
          moveVirtualCursorToOption();
          // Select the portion of the input text that is ahead of the user-inputted filter keyword
          // (this presents the type-ahead autocomplete)
          selectInputText(filterKeyword.length);
        }

        toggleListbox(filterKeyword && candidateCount > 0);
        toggleClearButton();
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
            toggleClearButton(true);
            dispatchInternalInputEvent();
            break;
          case 'ArrowUp':
            ev.preventDefault();
            toggleListbox(true);
            if (ev.altKey) {
              break;
            }
            selectOptionViaKeyboard(findPreviousSelectableOption());
            toggleClearButton(true);
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

      clearButton?.addEventListener('click', () => {
        input.value = '';
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

      function dispatchInternalInputEvent() {
        input.dispatchEvent(new Event('change', {bubbles: true}));
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
            () => indComboBox.toggleAttribute('open', true)
          );
          listbox.querySelector('[aria-selected=true]')?.scrollIntoView({block: 'nearest'});
        } else {
          abortPositioning?.();
          input.removeAttribute('aria-expanded');
          listbox.hidden = true;
          indComboBox.removeAttribute('open');
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
        if (!option) {
          return;
        }
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
        CustomElementBase.setValue(input, option?.dataset.value);
      }

      function moveVirtualCursorToOption(option) {
        // Omit the option to remove selection
        input.setAttribute('aria-activedescendant', option?.id || '');
        option.scrollIntoView({block: 'nearest'});
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
