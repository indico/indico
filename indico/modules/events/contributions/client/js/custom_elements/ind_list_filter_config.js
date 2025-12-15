// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Menu from 'indico/behaviors/menu';
import CustomElementBase from 'indico/custom_elements/_base';

import './ind_list_filter_config.scss';

class FieldVisibilitySettings {
  constructor(settingsField) {
    this.settingsField = settingsField;
    this.enabled = !!this.settingsField;
    const enabledFields = JSON.parse(this.settingsField?.value || '[]');
    const availableFields = JSON.parse(this.settingsField?.dataset.fields || '[]');
    this.fieldStates = new Map(
      availableFields.map(fieldId => [fieldId, enabledFields.includes(fieldId)])
    );
  }

  isVisible(fieldId) {
    return this.fieldStates.get(fieldId);
  }

  toggleVisible(fieldId, forceState = !this.isVisible(fieldId)) {
    this.fieldStates.set(fieldId, forceState);
    const visibleFieldIds = [];
    for (const [id, visible] of this.fieldStates) {
      if (visible) {
        visibleFieldIds.push(id);
      }
    }
    this.settingsField.value = JSON.stringify(visibleFieldIds);
    this.settingsField.dispatchEvent(new Event('change', {bubbles: true}));
  }
}

// Individual filter item custom element
CustomElementBase.defineWhenDomReady(
  'ind-list-filter',
  class extends CustomElementBase {
    static attributes = {
      fieldId: String,
      visible: Boolean,
      filterOnly: Boolean,
      active: Boolean,
    };

    setup() {
      const filterButton = this.querySelector('.filter-trigger');
      const filterList = this.querySelector('.filters');
      const visibilitySwitch = this.querySelector('.toggle-visibilty');
      new Menu(this, filterButton, filterList).setup();

      const markFilterState = () => {
        const hasAnyActiveItems = this.querySelectorAll(':checked').length > 0;
        this.active = hasAnyActiveItems;
      };

      if (this.filterOnly) {
        // Clicking the title opens the filter
        this.addEventListener('click', evt => {
          if (evt.target.closest('[data-main-trigger]')) {
            setTimeout(() => {
              filterButton.focus();
              filterButton.click();
            });
          }
        });
      } else {
        // Handle visibility toggle clicks
        this.addEventListener('click', evt => {
          if (!evt.target.closest('[data-main-trigger]')) {
            return;
          }

          this.visible = !this.visible;
          this.dispatchEvent(new Event('toggle-visibility', {bubbles: true}));
        });
      }

      this.addEventListener('change', evt => {
        if (evt.target.matches('input[type=checkbox]')) {
          markFilterState();
        }
      });

      visibilitySwitch.checked = this.visible;
      this.addEventListener('x-attrchange.visible', () => {
        visibilitySwitch.checked = this.visible;
      });

      markFilterState();
    }
  }
);

// Filter configuration dialog custom element
CustomElementBase.defineWhenDomReady(
  'ind-list-filter-config',
  class extends CustomElementBase {
    static filterId = 0;

    setup() {
      const fieldVisibilitySettings = new FieldVisibilitySettings(
        this.querySelector('input[name=visible_items]')
      );

      // The form dialog has a combination of overflow: hidden and auto.
      // Since the list filter is much larger when expanded, most of its
      // options would not be visible without changing the overflow property to visible.
      const popup = this.closest('.exclusivePopup');
      const dialog = popup?.parentElement;
      if (popup) {
        popup.style.overflow = 'visible';
      }
      if (dialog) {
        dialog.style.overflow = 'visible';
      }

      // Handle toggle-visibility events from child ind-list-filter elements
      if (fieldVisibilitySettings.enabled) {
        this.addEventListener('toggle-visibility', evt => {
          const {fieldId, visible} = evt.target;

          if (!fieldId) {
            return;
          }

          fieldVisibilitySettings.toggleVisible(fieldId, visible);
        });
      }

      // Clear filters button
      const resetBtn = this.querySelector('.reset-btn');
      resetBtn?.addEventListener('click', () => {
        this.querySelectorAll('input[type="checkbox"]:checked').forEach(checkbox => {
          checkbox.checked = false;
          checkbox.dispatchEvent(new Event('change', {bubbles: true}));
        });

        const message = this.querySelector('.clear-filters-message');
        if (message) {
          $(message).show({
            done() {
              setTimeout(() => {
                $(this).slideUp();
              }, 4000);
            },
          });
        }
      });

      // Tooltips for ellipsized titles
      this.querySelectorAll('.title').forEach(title => {
        title.addEventListener('mouseover', function() {
          if (this.offsetWidth < this.scrollWidth) {
            $(title)
              .qtip({hide: 'mouseout', content: title.textContent, overwrite: false})
              .qtip('show');
          }
        });
      });

      // Select all/none buttons
      const toggleFilterVisibility = visible => {
        this.querySelectorAll('ind-list-filter:not([filter-only])').forEach(filter => {
          filter.visible = visible;
          if (filter.fieldId) {
            fieldVisibilitySettings.toggleVisible(filter.fieldId, visible);
          }
        });
      };
      this.querySelector('#list-filter-select-all')?.addEventListener('click', () => {
        toggleFilterVisibility(true);
      });
      this.querySelector('#list-filter-select-none')?.addEventListener('click', () => {
        toggleFilterVisibility(false);
      });
    }

    activateFilter(filterEl) {
      const dropdown = filterEl.querySelector('.i-dropdown');
      const hasChecked = dropdown?.querySelectorAll(':checked').length > 0;
      filterEl.classList.toggle('active', hasChecked);
      filterEl.classList.toggle('highlight', hasChecked);
    }
  }
);
