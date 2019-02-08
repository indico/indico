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

import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Input} from 'semantic-ui-react';
import {DebounceInput} from 'react-debounce-input';
import {actions as filtersActions} from '../common/filters';

import './SearchBar.module.scss';


class SearchBar extends React.Component {
    static propTypes = {
        filters: PropTypes.object.isRequired,
        disabled: PropTypes.bool,
        actions: PropTypes.exact({
            setFilterParameter: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        disabled: false,
    };

    updateTextFilter = (filterValue) => {
        const {actions: {setFilterParameter}} = this.props;
        setFilterParameter('text', filterValue || null);
    };

    render() {
        const {filters: {text}, disabled} = this.props;
        let inputIcon;

        if (text) {
            inputIcon = <Icon link name="remove" onClick={() => this.updateTextFilter(null)} />;
        } else {
            inputIcon = <Icon name="search" />;
        }

        return (
            <div styleName="room-filters">
                <DebounceInput element={Input}
                               size="large"
                               styleName="text-filter"
                               icon={inputIcon}
                               debounceTimeout={400}
                               onChange={(event) => this.updateTextFilter(event.target.value)}
                               value={text || ''}
                               disabled={disabled} />
            </div>
        );
    }
}

export default (namespace, searchRoomsSelectors) => {
    return connect(
        state => ({
            filters: searchRoomsSelectors.getFilters(state),
        }),
        dispatch => ({
            actions: bindActionCreators({
                setFilterParameter: (param, value) => filtersActions.setFilterParameter(namespace, param, value),
            }, dispatch)
        })
    )(SearchBar);
};
