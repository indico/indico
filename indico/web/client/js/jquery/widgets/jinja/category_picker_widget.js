// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */
/* global build_url:false, handleAjaxError:false */

(function(global) {
  global.setupCategoryPickerWidget = function setupCategoryPickerWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        navigatorCategoryId: null,
        requireEventCreationRights: false,
        requireCategoryManagementRights: false,
        showEventCreationWarning: false,
      },
      options
    );

    const $field = $(`#${options.fieldId}`);
    const $categoryTitle = $(`#category-title-${options.fieldId}`);
    const $categoryWarning = $(`#category-warning-${options.fieldId}`);
    const $dialogTrigger = $(`#categorynav-button-${options.fieldId}`);
    let hiddenData = $field.val() ? JSON.parse($field.val()) : {};
    let navigatorCategory = options.navigatorCategoryId;
    const actionOn = {};

    if (options.requireEventCreationRights) {
      actionOn.categoriesWithoutEventCreationRights = {disabled: true};
    }

    if (options.requireCategoryManagementRights) {
      actionOn.categoriesWithoutCategoryManagementRights = {disabled: true};
    }

    if (hiddenData) {
      $categoryTitle.text(hiddenData.title);
      $field.val(JSON.stringify(hiddenData));
    }

    // null when we are in the root category and the root only has subcategories
    // See RHCreateEvent._default_category
    if (navigatorCategory !== null) {
      $.ajax({
        url: build_url(Indico.Urls.Categories.info, {category_id: navigatorCategory}),
        dataType: 'json',
        error: handleAjaxError,
        success(data) {
          navigatorCategory = data;
          const {category} = navigatorCategory;
          updateWarningVisibility(category);
        },
      });
    }

    $field.on('indico:categorySelected', (evt, category) => {
      updateWarningVisibility(category);
    });

    $dialogTrigger.on('click', function(evt) {
      evt.preventDefault();
      $('<div>').categorynavigator({
        category: navigatorCategory,
        openInDialog: true,
        actionOn,
        onAction(category) {
          const event = $.Event('indico:categorySelected');
          const dfd = $.Deferred();
          updateWarningVisibility(category);
          $categoryTitle.text(category.title);
          hiddenData = {id: category.id, title: category.title};
          navigatorCategory = category.id;
          $field
            .val(JSON.stringify(hiddenData))
            .trigger('change')
            .trigger(event, [category, dfd]);
          // jquery events are not compatible with normal DOM events, so we also trigger a normal
          // one so modern code can react to it
          $field[0].dispatchEvent(new Event('change', {bubbles: true}));
          if (event.isDefaultPrevented()) {
            return dfd;
          }
        },
      });
    });

    function updateWarningVisibility(category) {
      const hidden =
        !options.showEventCreationWarning ||
        !category || // unlisted event or no category selected
        !category.has_children ||
        category.has_events;
      $categoryWarning.toggleClass('hidden', hidden);
    }
  };
})(window);
