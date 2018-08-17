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
import {Button, Popup} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import * as blockingsActions from './actions';
import * as blockingsSelectors from './selectors';
import dateRenderer from '../../components/filters/DateRenderer';
import DateForm from '../../components/filters/DateForm';
import FilterDropdown from '../../components/filters/FilterDropdown';


const FilterBarContext = React.createContext();

function FilterDropdownFactory({name, ...props}) {
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


class BlockingFilterBar extends React.Component {
    static propTypes = {
        filters: PropTypes.shape({
            myBlockings: PropTypes.bool.isRequired,
            myRooms: PropTypes.bool.isRequired,
            dates: PropTypes.shape({
                startDate: PropTypes.string,
                endDate: PropTypes.string,
            }).isRequired,
        }).isRequired,
        actions: PropTypes.exact({
            setFilterParameter: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {};

    onDropdownOpen = (name) => {
        this.setState((prevState) => {
            return Object.assign(
                {},
                ...Object.keys(prevState).map(k => ({[k]: null})),
                {[name]: true}
            );
        });
    };

    onDropdownClose = (name) => {
        this.setState({
            [name]: false
        });
    };

    render() {
        const {filters: {myBlockings, myRooms, dates}, actions: {setFilterParameter}} = this.props;
        return (
            <FilterBarContext.Provider value={{
                onDropdownOpen: this.onDropdownOpen,
                onDropdownClose: this.onDropdownClose,
                state: this.state
            }}>
                <FilterDropdownFactory name="dates"
                                       title={<Translate>Period</Translate>}
                                       form={(fieldValues, setParentField, handleClose) => (
                                           <DateForm setParentField={setParentField}
                                                     handleClose={handleClose}
                                                     disabledDate={() => false}
                                                     isRange
                                                     {...dates} />
                                       )}
                                       setGlobalState={(value) => setFilterParameter('dates', value)}
                                       initialValues={dates}
                                       renderValue={dateRenderer}
                                       showButtons={false} />
                <Button.Group>
                    <Popup trigger={<Button content={Translate.string('Blockings in my rooms')}
                                            primary={myRooms}
                                            onClick={() => setFilterParameter('myRooms', !myRooms)} />}
                           content={Translate.string('Show only blockings in my rooms')} />
                    <Popup trigger={<Button content={Translate.string('My blockings')}
                                            primary={myBlockings}
                                            onClick={() => setFilterParameter('myBlockings', !myBlockings)} />}
                           content={Translate.string('Show only my blockings')} />
                </Button.Group>
            </FilterBarContext.Provider>
        );
    }
}

export default connect(
    state => ({
        filters: blockingsSelectors.getFilters(state),
    }),
    dispatch => ({
        actions: {
            setFilterParameter: (param, value) => {
                dispatch(blockingsActions.setFilterParameter(param, value));
                dispatch(blockingsActions.fetchBlockings());
            }
        }
    }),
)(BlockingFilterBar);
