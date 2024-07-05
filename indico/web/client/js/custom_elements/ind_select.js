// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {topBottomPosition} from 'indico/utils/positioning';

import './ind_select.scss';

customElements.define(
  'ind-select',
  class extends HTMLElement {
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

    connectedCallback() {
      const indSelect = this;
      const caption = this.querySelector('[data-caption]');
      const dialog = this.querySelector('dialog');
      const filter = dialog.querySelector('input');
      const listbox = dialog.querySelector('[role=listbox]');
      const optionList = listbox.querySelectorAll('[role=option]');
      const clear = this.querySelector('button[value=clear]');
      const id = `x-select-${this.constructor.lastId++}`;
      const defaultCaption = caption.textContent;
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

        if (evt.target.closest('[data-caption]') === caption) {
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
        setTimeout(function() {
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
        // to intercept focsout that fires before
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
          indSelect.setAttribute('aria-expanded', true);
          topBottomPosition(listbox, filter, {
            setStyle(target, targetWillFitBottom) {
              target.toggleAttribute('data-top', !targetWillFitBottom);
              filter.toggleAttribute('data-top', !targetWillFitBottom);
            },
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
        for (const option of optionList) {
          if (!keyword) {
            option.hidden = false;
          } else {
            const label = getOptionLabel(option).toLowerCase();
            option.hidden = !label.includes(keyword);
            if (label === keyword && !option.hasAttribute('aria-disabled')) {
              selectableOption = option;
            }
          }
        }
        if (selectableOption) {
          selectOption(selectableOption);
          dispatchChange();
        }
      }

      function selectNextOption() {
        selectOptionWithIndex(function(currentIndex, optionCount) {
          return (currentIndex + 1) % optionCount;
        });
      }

      function selectPreviousOption() {
        selectOptionWithIndex(function(currentIndex, optionCount) {
          if (currentIndex <= 0) {
            return optionCount - 1;
          }
          return currentIndex - 1;
        });
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
        const optionLabel = getOptionLabel($option);
        caption.textContent = optionLabel;
        filter.placeholder = optionLabel;
        setValue($option.dataset.value);
      }

      function clearValue() {
        unmarkSelectedOption();
        caption.textContent = defaultCaption;
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
            'Please select an item in the list.'
          );
        }
      }

      // Should always be called after user-initiated change in value
      function dispatchChange() {
        indSelect.dispatchEvent(new Event('change', {bubbles: true}));
      }

      function getOptionLabel($option) {
        return (
          $option.querySelector('[data-label]')?.textContent ??
          $option.getAttribute('aria-label') ??
          $option.textContent
        );
      }
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
