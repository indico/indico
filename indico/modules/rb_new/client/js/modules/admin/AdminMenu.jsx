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
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {Link, NavLink, withRouter} from 'react-router-dom';
import {Icon, Menu, Placeholder} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {Translate} from 'indico/react/i18n';
import * as adminSelectors from './selectors';
import * as adminActions from './actions';

import './AdminMenu.module.scss';


function renderMenuPlaceholder() {
    return (
        <Menu vertical>
            <Menu.Item>
                <Menu.Header>
                    <Placeholder>
                        <Placeholder.Line length="medium" />
                    </Placeholder>
                </Menu.Header>
                <Menu.Menu>
                    <Menu.Item>
                        <Placeholder>
                            <Placeholder.Line length="short" />
                            <Placeholder.Line length="short" />
                            <Placeholder.Line length="short" />
                            <Placeholder.Line length="short" />
                        </Placeholder>
                    </Menu.Item>
                </Menu.Menu>
            </Menu.Item>
        </Menu>
    );
}

function AdminMenu({locations, isFetchingLocations, actions: {clearTextFilter}}) {
    if (isFetchingLocations) {
        return renderMenuPlaceholder();
    }

    const hasLocations = locations.length !== 0;
    const locationURL = (locationId) => `/admin/locations/${locationId}`;
    return (
        <Menu size="large" styleName="admin-menu" vertical>
            <Menu.Item>
                <NavLink exact to="/admin">
                    <Translate>General settings</Translate>
                </NavLink>
            </Menu.Item>
            <Menu.Item>
                <Menu.Header>
                    <Translate>Room Metadata</Translate>
                </Menu.Header>
                <Menu.Menu>
                    <Menu.Item>
                        <NavLink exact to="/admin/attributes">
                            <Translate>Attributes</Translate>
                        </NavLink>
                    </Menu.Item>
                    <Menu.Item>
                        <NavLink exact to="/admin/equipment">
                            <Translate>Equipment & Features</Translate>
                        </NavLink>
                    </Menu.Item>
                </Menu.Menu>
            </Menu.Item>
            <Menu.Item>
                <Menu.Header styleName="locations-header">
                    <Translate>Locations</Translate>
                    <Link to="/admin/locations/"><Icon name="setting" /></Link>
                </Menu.Header>
                {hasLocations && (
                    <Menu.Menu>
                        {locations.map((location) => (
                            <Menu.Item key={location.id}>
                                <NavLink to={locationURL(location.id)}
                                         onClick={clearTextFilter}
                                         exact>
                                    {location.name}
                                </NavLink>
                            </Menu.Item>
                        ))}
                    </Menu.Menu>
                )}
            </Menu.Item>
        </Menu>
    );
}

AdminMenu.propTypes = {
    locations: PropTypes.array.isRequired,
    isFetchingLocations: PropTypes.bool.isRequired,
    actions: PropTypes.exact({
        clearTextFilter: PropTypes.func.isRequired,
    }).isRequired,
};


export default withRouter(connect(
    (state) => ({
        locations: adminSelectors.getAllLocations(state),
        isFetchingLocations: adminSelectors.isFetchingLocations(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            clearTextFilter: adminActions.clearTextFilter,
        }, dispatch),
    })
)(AdminMenu));
