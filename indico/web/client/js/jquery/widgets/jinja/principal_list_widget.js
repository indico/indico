// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupPrincipalListWidget = function setupPrincipalListWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        eventId: null,
        openImmediately: false,
        groups: null,
        allowExternal: false,
        allowNetworks: false,
        networks: [],
      },
      options
    );

    var field = $('#' + options.fieldId);
    var principals = JSON.parse(field.val());

    function addPrincipal(newPrincipals, setResult) {
      // remove existing ones first to avoid duplicates
      newPrincipals = _.filter(newPrincipals, function(principal) {
        return !_.findWhere(principals, {identifier: principal.identifier});
      });
      principals = _.sortBy(principals.concat(newPrincipals), function(principal) {
        var weight =
          principal._type == 'Avatar'
            ? 0
            : principal._type == 'Email'
            ? 1
            : principal.isGroup
            ? 2
            : 3;
        var name = principal._type !== 'Email' ? principal.name : principal.email;
        return [weight, name.toLowerCase()];
      });
      field.val(JSON.stringify(principals));
      field.trigger('change');
      setResult(true, principals);
    }

    function removePrincipal(principal, setResult) {
      principals = _.without(
        principals,
        _.findWhere(principals, {
          identifier: principal.get('identifier'),
        })
      );
      field.val(JSON.stringify(principals));
      field.trigger('change');
      setResult(true);
    }

    var widget = new UserListField(
      'PluginOptionPeopleListDiv',
      'user-list',
      principals,
      true,
      null,
      true,
      options.groups,
      options.eventId,
      null,
      false,
      false,
      false,
      // Disable favorite button for EventPerson mode
      options.eventId !== null,
      addPrincipal,
      userListNothing,
      removePrincipal,
      options.allowExternal,
      options.allowNetworks,
      options.networks
    );

    $E('userGroupList-' + options.fieldId).set(widget.draw());

    if (options.openImmediately) {
      $('#userGroupList-' + options.fieldId + ' input[type=button]').trigger('click');
    }
  };
})(window);
