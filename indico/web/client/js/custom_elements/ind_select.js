// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

import CustomElementBase from 'indico/custom_elements/_base';
import {Translate} from 'indico/react/i18n';
import * as positioning from 'indico/utils/positioning';

import './ind_select.scss';

customElements.define(
  'ind-select',
  class extends CustomElementBase {
    static formAssociated = true;

    static lastId = 1;

    get value() {
      return this.getAttribute('value');
    }

    set value(value) {
      this.setAttribute('value', value);
    }

    get open() {
      return this.hasAttribute('open');
    }

    set open(isOpen) {
      this.toggleAttribute('open', isOpen);
    }

    get required() {
      return this.hasAttribute('required');
    }

    set required(isRequired) {
      this.toggleAttribute('required', isRequired);
    }

    setup() {
      const indSelect = this;
      const caption = this.querySelector('[data-caption]');
      const dialog = this.querySelector('dialog');
      const filter = dialog.querySelector('input');
      const listbox = dialog.querySelector('[role=listbox]');
      const optionList = listbox.querySelectorAll('[role=option]');
      const noOptionFoundMessage = listbox.querySelector('.no-option');
      const clear = this.querySelector('button[value=clear]');
      const id = `x-select-${this.constructor.lastId++}`;
      const defaultCaption = caption.innerHTML;
      const internals = this.attachInternals();

      // Prepare the initial state

      optionList.forEach((option, idx) => {
        option.id = `${id}-${idx}`;
        if (option.dataset.value === this.value) {
          selectOption(option);
        }
      });

      dialog.id = `${id}-dialog`;
      indSelect.tabIndex = 0;
      indSelect.setAttribute('aria-controls', dialog.id);
      indSelect.setAttribute('aria-haspopup', 'listbox');
      filter.setAttribute('aria-autocomplete', 'listbox');
      indSelect.role = 'combobox';
      if (this.required) {
        this.setAttribute('aria-required', true);
      }
      applyConstraintValidation();

      // Event listeners

      indSelect.addEventListener('click', evt => {
        // Test for clicks that caused the dialog to close
        // so that we do not immediately reopen.
        if (indSelect._closedViaFocusout) {
          return;
        }

        if (evt.target.closest('[data-caption]') === caption || evt.target === evt.currentTarget) {
          toggleListbox();
        }
      });

      indSelect.addEventListener('keydown', evt => {
        if (indSelect.open || evt.target !== evt.currentTarget) {
          return;
        }

        if (evt.code === 'Enter' || evt.code === 'Space') {
          evt.preventDefault();
          toggleListbox();
        }
      });

      dialog.addEventListener('focusout', () => {
        if (dialog.contains(document.activeElement)) {
          return;
        }
        toggleListbox(false);
        indSelect._closedViaFocusout = true;
        setTimeout(() => {
          delete indSelect._closedViaFocusout;
        }, 200);
      });

      indSelect.addEventListener('keydown', evt => {
        if (evt.code === 'ArrowDown') {
          toggleListbox(true);
          if (!evt.altKey) {
            selectNextOption();
          }
        } else if (evt.code === 'ArrowUp') {
          toggleListbox(true);
          selectPreviousOption();
        }
      });

      dialog.addEventListener('keydown', ev => {
        if (ev.code === 'Escape' || ev.code === 'Enter') {
          ev.preventDefault();
          toggleListbox(false);
        }
      });

      filter.addEventListener('input', evt => {
        // The user of this custom element is expected to handle
        // events related to changes in the value. To avoid confusion
        // we don't want to leak events that would make event handling
        // ambiguous. Therefore, we suppress the 'input' and 'change'
        // events coming from the filter field.
        evt.stopPropagation();
        const keyword = filter.value.trim().toLowerCase();
        applyFilter(keyword);
      });

      filter.addEventListener('change', evt => {
        // The user of this custom element is expected to handle
        // events related to changes in the value. To avoid confusion
        // we don't want to leak events that would make event handling
        // ambiguous. Therefore, we suppress the 'input' and 'change'
        // events coming from the filter field.
        evt.stopPropagation();
      });

      filter.addEventListener('keydown', evt => {
        if (evt.code === 'ArrowUp' || evt.code === 'ArrowDown') {
          evt.preventDefault();
        }
      });

      listbox.addEventListener('pointerdown', evt => {
        // Instead of click we use pointerdown
        // to intercept focusout that fires before
        // click, closing the dialog and making the
        // target option unavailable before selection.
        const $option = evt.target.closest('[role=option]');
        if ($option) {
          selectOption($option);
          dispatchChange();
        }
      });

      clear?.addEventListener('click', () => {
        clearValue();
        indSelect.focus();
        dispatchChange();
      });

      indSelect.addEventListener('x-attrchange:value', () => {
        for (const option of optionList) {
          if (option.dataset.value === indSelect.value) {
            selectOption(option);
            return;
          }
        }
        clearValue();
      });

      // Internal functions

      function toggleListbox(shouldOpen = !indSelect.open) {
        indSelect.open = shouldOpen;
        if (shouldOpen) {
          dialog.show();
          positioning.position(listbox, indSelect, positioning.dropdownPositionStrategy, fit => {
            indSelect.setAttribute('aria-expanded', true);
            filter.toggleAttribute('data-top', !fit);
          });
        } else {
          dialog.close();
          indSelect.setAttribute('aria-expanded', false);
          applyFilter('');
          filter.value = '';
        }
      }

      function applyFilter(keyword) {
        let selectableOption;
        let numMatches = 0;
        for (const option of optionList) {
          if (!keyword) {
            option.hidden = false;
            numMatches++;
          } else {
            const label = getOptionLabelText(option).toLowerCase();
            option.hidden = !_.deburr(label).includes(_.deburr(keyword));
            numMatches += Number(!option.hidden);
            if (label === keyword && !option.hasAttribute('aria-disabled')) {
              selectableOption = option;
            }
          }
        }
        if (selectableOption) {
          selectOption(selectableOption);
          dispatchChange();
        }
        noOptionFoundMessage.hidden = !!numMatches;
      }

      function selectNextOption() {
        selectOptionWithIndex((currentIndex, optionCount) => (currentIndex + 1) % optionCount);
      }

      function selectPreviousOption() {
        selectOptionWithIndex((currentIndex, optionCount) =>
          currentIndex <= 0 ? optionCount - 1 : currentIndex - 1
        );
      }

      function selectOption(option) {
        unmarkSelectedOption();
        markSelectedOption(option);
      }

      function selectOptionWithIndex(getIndex) {
        const $currentOption = unmarkSelectedOption();
        const $$selectableOptions = [
          ...listbox.querySelectorAll('[role=option]:not([hidden]):not([aria-disabled])'),
        ];
        const currentIndex = $$selectableOptions.indexOf($currentOption);
        const nextIndex = getIndex(currentIndex, $$selectableOptions.length);
        const $nextOption = $$selectableOptions[nextIndex];
        markSelectedOption($nextOption);
        dispatchChange();
        $nextOption.scrollIntoView({block: 'nearest'});
      }

      function unmarkSelectedOption() {
        const $currentOption = listbox.querySelector('[aria-selected]');
        $currentOption?.removeAttribute('aria-selected');
        return $currentOption;
      }

      function markSelectedOption($option) {
        $option.setAttribute('aria-selected', true);
        filter.setAttribute('aria-activedescendant', $option.id);
        indSelect.setAttribute('aria-activedescendant', $option.id);
        caption.innerHTML = $option.innerHTML;
        filter.placeholder = getOptionLabelText($option);
        setValue($option.dataset.value);
      }

      function clearValue() {
        unmarkSelectedOption();
        caption.innerHTML = defaultCaption;
        filter.placeholder = '';
        setValue('');
      }

      function setValue(value) {
        internals.setFormValue(value);
        indSelect.value = value;
        applyConstraintValidation();

        if (!indSelect.required && clear) {
          clear.hidden = !indSelect.value;
        }
      }

      function applyConstraintValidation() {
        if (indSelect.required) {
          internals.setValidity(
            {valueMissing: !indSelect.value},
            Translate.string('Please select an item in the list.')
          );
        }
      }

      // Should always be called after user-initiated change in value
      function dispatchChange() {
        indSelect.dispatchEvent(new Event('change', {bubbles: true}));
      }

      function getOptionLabelText($option) {
        return (
          $option.querySelector('[data-label]')?.textContent ??
          $option.getAttribute('aria-label') ??
          $option.textContent
        );
      }
    }

    focus() {
      this.click();
    }

    static observedAttributes = ['value'];

    attributeChangedCallback(name, previousValue, newValue) {
      if (previousValue === newValue) {
        return;
      }
      this.dispatchEvent(new Event(`x-attrchange:${name}`));
    }
  }
);
