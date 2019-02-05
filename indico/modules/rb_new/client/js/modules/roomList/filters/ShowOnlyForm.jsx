/* This file is part of Indico.
* Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
*
* Indico is free software; you can redistribute it and/or
* modify it under the terms of the GNU General Public License as
* published by the Free Software Foundation; either version 3 of the
* License, or (at your option) any later version.
*
* Indico is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with Indico; if not, see <http://www.gnu.org/licenses/>.
*/

import React from 'react';
import {connect} from 'react-redux';
import {Checkbox, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {selectors as userSelectors} from '../../../common/user';
import {FilterFormComponent} from '../../../common/filters';
import * as roomsSelectors from '../selectors';

import './ShowOnlyForm.module.scss';


class ShowOnlyForm extends FilterFormComponent {
    render() {
        const {
            filters: {onlyFavorites, onlyMine, onlyAuthorized},
            onlyFavorites: newOnlyFavorites, onlyMine: newOnlyMine, onlyAuthorized: newOnlyAuthorized,
            hasFavoriteRooms, hasOwnedRooms, setParentField, showOnlyAuthorizedFilter, disabled,
            hasUnbookableRooms,
        } = this.props;

        return (
            <>
                <div styleName="show-only-filter">
                    <Checkbox onChange={(__, {checked}) => setParentField('onlyFavorites', checked)}
                              disabled={(!onlyFavorites && !hasFavoriteRooms) || disabled}
                              checked={newOnlyFavorites}
                              toggle />
                    <Icon name="star" />
                    <span>
                        <Translate>My favorite rooms</Translate>
                    </span>
                </div>
                {(hasOwnedRooms || onlyMine) && (
                    <div styleName="show-only-filter">
                        <Checkbox onChange={(__, {checked}) => setParentField('onlyMine', checked)}
                                  disabled={disabled}
                                  checked={newOnlyMine}
                                  toggle />
                        <Icon name="user" />
                        <span>
                            <Translate>Rooms I manage</Translate>
                        </span>
                    </div>
                )}
                {showOnlyAuthorizedFilter && (hasUnbookableRooms || onlyAuthorized) && (
                    <div styleName="show-only-filter">
                        <Checkbox onChange={(__, {checked}) => setParentField('onlyAuthorized', checked)}
                                  disabled={disabled}
                                  checked={newOnlyAuthorized}
                                  toggle />
                        <Icon name="lock open" />
                        <span>
                            <Translate>Rooms I am authorized to book</Translate>
                        </span>
                    </div>
                )}
            </>
        );
    }
}

export default connect(
    state => ({
        filters: roomsSelectors.getFilters(state),
        hasOwnedRooms: userSelectors.hasOwnedRooms(state),
        hasFavoriteRooms: userSelectors.hasFavoriteRooms(state),
        hasUnbookableRooms: userSelectors.hasUnbookableRooms(state),
    })
)(ShowOnlyForm);
