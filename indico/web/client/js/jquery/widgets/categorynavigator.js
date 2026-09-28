// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {
  renderInlineCategoryNavigator,
  showCategoryNavigator,
  unmountInlineCategoryNavigator,
} from 'indico/react/components/category_navigator';
import {$T} from 'indico/utils/i18n';

(function($) {
  $.widget('indico.categorynavigator', {
    options: {
      category: 0,
      actionButtonText: $T.gettext('Select'),
      confirmation: false,
      emptyCategoryText: $T.gettext("This category doesn't contain any subcategory"),
      openInDialog: false,
      dialogTitle: $T.gettext('Select a category'),
      dialogSubtitle: null,
      actionOn: {
        categoriesWithoutEventProposalRights: {
          disabled: false,
          message: $T.gettext('Not possible for categories where you cannot propose events'),
        },
        categoriesWithoutEventProposalOrCreationRights: {
          disabled: false,
          message: $T.gettext('Not possible for categories where you cannot propose/create events'),
        },
        categoriesWithoutEventCreationRights: {
          disabled: false,
          message: $T.gettext('Not possible for categories where you cannot create events'),
        },
        categoriesWithoutCategoryManagementRights: {
          disabled: false,
          message: $T.gettext('Not possible for categories where you are not a manager'),
        },
        categoriesDescendingFrom: {
          disabled: false,
          ids: [],
          // The closest parent category title will be used if more than one parent is present in ids
          message: $T.gettext('Not possible for categories descending from category "{0}"'),
        },
        categories: {
          disabled: false,
          message: $T.gettext('Not possible for this category'),
          ids: [],
          // Expects an Array of {ids: [...], message: '...'} for more specific messages
          groups: [],
        },
      },
      isNavigation: false,
      actionUrl: null,
      onAction() {},
    },

    _create() {
      const self = this;
      self._api = {current: null};
      const options = {...self.options, apiRef: self._api};
      if (self.options.openInDialog) {
        showCategoryNavigator(options);
      } else {
        renderInlineCategoryNavigator(self.element[0], options);
      }
    },

    _destroy() {
      if (!this.options.openInDialog) {
        unmountInlineCategoryNavigator(this.element[0]);
      }
    },

    goToCategory(id) {
      this._api.current?.goToCategory(id);
    },

    searchCategories(query) {
      this._api.current?.searchCategories(query);
    },
  });
})(jQuery);
