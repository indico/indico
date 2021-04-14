// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  global.setupSortableList = function setupSortableList($wrapper) {
    /* Works with the sortable_lists and sortable_list macros defined in
     * web/templates/_sortable_list.html
     */

    if (
      $wrapper.filter('.disable-if-locked').closest('.event-locked').length ||
      $wrapper.closest('.disable-if-locked').closest('.event-locked').length
    ) {
      return;
    }

    // Render the lists sortable
    if ($wrapper.data('disable-dragging') === undefined) {
      var $lists = $wrapper.find('ul');
      $lists.sortable({
        connectWith: $lists,
        placeholder: 'i-label sortable-item placeholder',
        containment: $wrapper,
        tolerance: 'pointer',
        forcePlaceholderSize: true,
      });
    }

    // Move an item from the enabled list to the disabled one (or vice versa).
    function toggleEnabled($li) {
      var $list = $li.closest('ul');
      var targetClass = $list.hasClass('enabled') ? '.disabled' : '.enabled';
      var $destination = $list.closest('.js-sortable-list-widget').find('ul' + targetClass);
      $li.detach().appendTo($destination);
    }

    $wrapper.find('ul li .toggle-enabled').on('click', function() {
      toggleEnabled($(this).closest('li'));
    });

    // Prevents dragging the row when the action buttons are clicked.
    $wrapper.find('.actions').on('mousedown', function(evt) {
      evt.stopPropagation();
    });
  };
})(window);
