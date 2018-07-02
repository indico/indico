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
import {Button, Icon, Label, Popup} from 'semantic-ui-react';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import FilterDropdown from './filters/FilterDropdown';
import CapacityForm from './filters/CapacityForm';
import EquipmentForm from './filters/EquipmentForm';

import './RoomFilterBar.module.scss';


const FilterBarContext = React.createContext();

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

// eslint-disable-next-line react/prop-types
const capacityRenderer = ({capacity}) => (
    (capacity === null)
        ? null : (
            <span>
                <Icon name="user" />
                {capacity}
            </span>
        ));

const equipmentRenderer = ({equipment}) => {
    if (equipment.length) {
        return (
            <>
                <Translate>Equipment</Translate>
                <Label circular horizontal className="white" size="medium" styleName="filter-bar-button-label">
                    {equipment.length}
                </Label>
            </>
        );
    } else {
        return null;
    }
};

export const equipmentType = PropTypes.array;

export default class RoomFilterBar extends React.Component {
    static propTypes = {
        equipmentTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
        capacity: PropTypes.number,
        equipment: equipmentType,
        onlyFavorites: PropTypes.bool,
        onlyMine: PropTypes.bool,
        hasFavoriteRooms: PropTypes.bool,
        hasOwnedRooms: PropTypes.bool,
        setFilterParameter: PropTypes.func.isRequired,
        children: PropTypes.node
    };

    static defaultProps = {
        capacity: null,
        onlyFavorites: false,
        onlyMine: false,
        hasFavoriteRooms: false,
        hasOwnedRooms: false,
        children: null,
        equipment: [],
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
        const {
            capacity, onlyFavorites, onlyMine, children, equipment, setFilterParameter, equipmentTypes,
            hasOwnedRooms, hasFavoriteRooms
        } = this.props;


        const equipmentFilter = !!equipmentTypes.length && (
            <FilterDropdownFactory name="equipment"
                                   title={<Translate>Equipment</Translate>}
                                   form={({equipment: selectedEquipment}, setParentField) => (
                                       <EquipmentForm setParentField={setParentField}
                                                      selectedEquipment={selectedEquipment}
                                                      possibleEquipment={equipmentTypes} />
                                   )}
                                   counter
                                   setGlobalState={data => setFilterParameter('equipment', data.equipment)}
                                   initialValues={{equipment}}
                                   renderValue={equipmentRenderer} />
        );

        return (
            <Button.Group size="large">
                <FilterBarContext.Provider value={{
                    onDropdownOpen: this.onDropdownOpen,
                    onDropdownClose: this.onDropdownClose,
                    state: this.state
                }}>
                    {children}
                    <FilterDropdownFactory name="capacity"
                                           title={<Translate>Min. Capacity</Translate>}
                                           form={({capacity: selectedCapacity}, setParentField) => (
                                               <CapacityForm setParentField={setParentField}
                                                             capacity={selectedCapacity} />
                                           )}
                                           setGlobalState={data => setFilterParameter('capacity', data.capacity)}
                                           initialValues={{capacity}}
                                           renderValue={capacityRenderer} />
                    {equipmentFilter}
                    {(hasOwnedRooms || onlyMine) && (
                        <Popup trigger={<Button icon="user" primary={onlyMine}
                                                onClick={() => setFilterParameter('onlyMine', !onlyMine)} />}
                               content={Translate.string('Show only rooms I manage')} />
                    )}
                    <Popup trigger={<Button icon="star" primary={onlyFavorites}
                                            disabled={!onlyFavorites && !hasFavoriteRooms}
                                            onClick={() => setFilterParameter('onlyFavorites', !onlyFavorites)} />}
                           content={Translate.string('Show only my favorite rooms')} />
                </FilterBarContext.Provider>
            </Button.Group>
        );
    }
}
