// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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

    if (hiddenData) {
      $categoryTitle.text(hiddenData.title);
      $field.val(JSON.stringify(hiddenData));
    }

    $.ajax({
      url: build_url(Indico.Urls.Categories.info, {category_id: navigatorCategory}),
      dataType: 'json',
      error: handleAjaxError,
      success(data) {
        navigatorCategory = data;
        const {category} = navigatorCategory;
        $categoryWarning.toggleClass('hidden', !category.has_children || category.has_events);
      },
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
          $categoryWarning.toggleClass('hidden', !category.has_children || category.has_events);
          $categoryTitle.text(category.title);
          hiddenData = {id: category.id, title: category.title};
          navigatorCategory = category.id;
          $field
            .val(JSON.stringify(hiddenData))
            .trigger('change')
            .trigger(event, [category, dfd]);
          if (event.isDefaultPrevented()) {
            return dfd;
          }
        },
      });
    });
  };
})(window);
