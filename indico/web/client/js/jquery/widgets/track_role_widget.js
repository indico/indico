// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {TrackACLField} from 'indico/react/components';

(function($) {
  $.widget('indico.trackrolewidget', {
    options: {
      containerElement: null, // the actual widget containing element
      permissionsInfo: null,
      eventId: null,
      eventRoles: null,
      categoryRoles: null,
    },

    _updateValue(newValue, trackId) {
      const roleData = JSON.parse(this.element.val());
      roleData[trackId] = newValue;
      this.element.val(JSON.stringify(roleData));
    },

    _renderACLField(trackId, value) {
      const onChange = newValue => this._updateValue(newValue, trackId);
      const element = document.querySelector(`#track-roles-${trackId}`);
      const component = React.createElement(TrackACLField, {
        value,
        permissionInfo: this.options.permissionsInfo,
        eventId: this.options.eventId,
        eventRoles: this.options.eventRoles,
        categoryRoles: this.options.categoryRoles,
        scrollOnOpen: true,
        onChange,
      });
      ReactDOM.render(component, element);
    },

    _create() {
      const roleData = JSON.parse(this.element.val());
      Object.entries(roleData).forEach(([trackId, value]) => {
        trackId = trackId === '*' ? 'global' : trackId;
        this._renderACLField(trackId, value);
      });
    },
  });
})(jQuery);
