// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {connect} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import {Checkbox} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {FilterFormComponent} from '../../../common/filters';
import {selectors as userSelectors} from '../../../common/user';
import * as roomsSelectors from '../selectors';

import './ShowOnlyForm.module.scss';

class ShowOnlyForm extends FilterFormComponent {
  render() {
    const {
      filters: {onlyFavorites, onlyMine, onlyAuthorized},
      onlyFavorites: newOnlyFavorites,
      onlyMine: newOnlyMine,
      onlyAuthorized: newOnlyAuthorized,
      hasFavoriteRooms,
      hasOwnedRooms,
      setParentField,
      showOnlyAuthorizedFilter,
      disabled,
      hasUnbookableRooms,
      hideFavoritesFilter,
    } = this.props;

    return (
      <>
        {!hideFavoritesFilter && (
          <div styleName="show-only-filter">
            <Checkbox
              onChange={(__, {checked}) => setParentField('onlyFavorites', checked)}
              disabled={(!onlyFavorites && !hasFavoriteRooms) || disabled}
              checked={newOnlyFavorites}
              showAsToggle
              label={
                <>
                  <Icon name="star" />
                  <span>
                    <Translate>My favorite rooms</Translate>
                  </span>
                </>
              }
            />
          </div>
        )}
        {(hasOwnedRooms || onlyMine) && (
          <div styleName="show-only-filter">
            <Checkbox
              onChange={(__, {checked}) => setParentField('onlyMine', checked)}
              disabled={disabled}
              checked={newOnlyMine}
              showAsToggle
              label={
                <>
                  <Icon name="user" />
                  <span>
                    <Translate>Rooms I manage</Translate>
                  </span>
                </>
              }
            />
          </div>
        )}
        {showOnlyAuthorizedFilter && (hasUnbookableRooms || onlyAuthorized) && (
          <div styleName="show-only-filter">
            <Checkbox
              onChange={(__, {checked}) => setParentField('onlyAuthorized', checked)}
              disabled={disabled}
              checked={newOnlyAuthorized}
              showAsToggle
              label={
                <>
                  <Icon name="lock open" />
                  <span>
                    <Translate>Rooms I am authorized to book</Translate>
                  </span>
                </>
              }
            />
          </div>
        )}
      </>
    );
  }
}

export default connect(state => ({
  filters: roomsSelectors.getFilters(state),
  hasOwnedRooms: userSelectors.hasOwnedRooms(state),
  hasFavoriteRooms: userSelectors.hasFavoriteRooms(state),
  hasUnbookableRooms: userSelectors.hasUnbookableRooms(state),
}))(ShowOnlyForm);
