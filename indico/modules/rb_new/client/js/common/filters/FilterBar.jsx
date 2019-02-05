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
import FilterDropdown from './FilterDropdown';


export const FilterBarContext = React.createContext();


export function FilterDropdownFactory({name, ...props}) {
    return (
        <FilterBarContext.Consumer>
            {({state, onDropdownOpen, onDropdownClose}) => (
                <FilterDropdown open={state[name]}
                                onOpen={() => onDropdownOpen(name)}
                                onClose={() => onDropdownClose(name)}
                                {...props} />
            )}
        </FilterBarContext.Consumer>
    );
}

FilterDropdownFactory.propTypes = {
    name: PropTypes.string.isRequired
};


export class FilterBarController extends React.Component {
    static propTypes = {
        children: PropTypes.node.isRequired
    };

    state = {};

    onDropdownOpen = (name) => {
        this.setState(
            (prevState) => Object.assign({}, ...Object.keys(prevState).map(k => ({[k]: null})), {[name]: true}));
    };

    onDropdownClose = (name) => {
        this.setState({
            [name]: false
        });
    };

    render() {
        const {children} = this.props;
        return (
            <FilterBarContext.Provider value={{
                onDropdownOpen: this.onDropdownOpen,
                onDropdownClose: this.onDropdownClose,
                state: this.state
            }}>
                {children}
            </FilterBarContext.Provider>
        );
    }
}
