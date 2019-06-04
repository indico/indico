// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  'use strict';

  $.widget('indico.trackrolewidget', {
    options: {
      containerElement: null, // the actual widget containing element
      userData: {}, // map of user data by id
    },

    _setUpRoleContainer: function($container) {
      var self = this;
      var $addUserButton = $container.find('.add-user');
      var $field = $container.find('.js-user-data');
      var role = $container.data('roleId');
      var track = $container.closest('.js-track-config').data('trackId');
      var roleData = self.roleData[track][role];

      $field.val(JSON.stringify(_.map(roleData, _.propertyOf(self.options.userData))));
      $field.principalfield({
        allowExternalUsers: false,
        multiChoice: true,
        overwriteChoice: false,

        render: function(people) {
          var $placeholder = $container.find('.placeholder');
          var $list = $container.find('.user-role-list').empty();

          $placeholder.toggle(!people.length);
          _.sortBy(people, _.property('name')).forEach(function(person) {
            $list.append(
              $('<li class="event-user">')
                .text(person.name)
                .append('<a class="remove-user icon-cross hide-if-locked">')
                .attr('data-user-id', +person.id)
            );
          });
        },

        onAdd: function(people) {
          people.forEach(function(person) {
            // XXX: person.id is a string for users from search results
            roleData.push(+person.id);
            self._update();
          });
        },
      });

      $container.on('click', '.remove-user', function(evt) {
        evt.preventDefault();
        var $userElement = $(this).closest('li');
        var userId = $userElement.data('userId');
        $userElement.remove();
        roleData = self.roleData[track][role] = _.without(roleData, userId);
        self._update();
        $field.principalfield('removeOne', userId);
      });

      $addUserButton.on('click', function(evt) {
        evt.preventDefault();
        $field.principalfield('choose');
      });
    },

    _update: function() {
      this.element.val(JSON.stringify(this.roleData));
    },

    _setUp: function($trackConfig) {
      var self = this;
      $trackConfig.find('.js-role-container').each(function() {
        self._setUpRoleContainer($(this));
      });
    },

    _create: function() {
      var self = this;
      var $container = self.options.containerElement;
      self.roleData = JSON.parse(self.element.val());
      $container.find('.js-track-config').each(function() {
        self._setUp($(this));
      });
    },
  });
})(jQuery);
