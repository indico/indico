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
import {Button, Icon, Label} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';

import {Translate, Param} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';

import CapacityForm from './filters/CapacityForm';
import EquipmentForm from './filters/EquipmentForm';
import BuildingForm from './filters/BuildingForm';
import ShowOnlyForm from './filters/ShowOnlyForm';
import {FilterBarController, FilterDropdownFactory} from '../../common/filters/FilterBar';
import {actions as filtersActions} from '../../common/filters';
import {selectors as userSelectors} from '../../common/user';

import {selectors as roomsSelectors} from '../../common/rooms';
import './RoomFilterBar.module.scss';


// eslint-disable-next-line react/prop-types
const renderCapacity = ({capacity}) => (
    (capacity === null)
        ? null : (
            <span>
                <Icon name="user" />
                {capacity}
            </span>
        ));

// eslint-disable-next-line react/prop-types
const renderEquipment = ({equipment, features}) => {
    const count = equipment.length + features.length;
    if (!count) {
        return null;
    }
    return (
        <>
            <Translate>Equipment</Translate>
            <Label circular horizontal className="white" size="tiny" styleName="filter-bar-button-label">
                {count}
            </Label>
        </>
    );
};

// eslint-disable-next-line react/prop-types
const renderBuilding = ({building}) => {
    if (!building) {
        return null;
    }

    return (
        <>
            <Icon name="building" />
            <Translate>
                Building <Param name="building" value={building} />
            </Translate>
        </>
    );
};

export class RoomFilterBarBase extends React.Component {
    static propTypes = {
        equipmentTypes: PropTypes.arrayOf(PropTypes.string).isRequired,
        features: PropTypes.arrayOf(PropTypes.shape({
            icon: PropTypes.string.isRequired,
            name: PropTypes.string.isRequired,
            title: PropTypes.string.isRequired,
        })).isRequired,
        buildings: PropTypes.array.isRequired,
        showOnlyAuthorizedFilter: PropTypes.bool,
        extraButtons: PropTypes.node,
        hasOwnedRooms: PropTypes.bool.isRequired,
        filters: PropTypes.shape({
            building: PropTypes.string,
            capacity: PropTypes.number,
            equipment: PropTypes.array,
            onlyFavorites: PropTypes.bool,
            onlyMine: PropTypes.bool,
            onlyAuthorized: PropTypes.bool,
            features: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
        actions: PropTypes.shape({
            setFilterParameter: PropTypes.func,
            setFilters: PropTypes.func,
        }).isRequired,
        hideOptions: PropTypes.objectOf(PropTypes.bool),
        disabled: PropTypes.bool,
    };

    static defaultProps = {
        showOnlyAuthorizedFilter: true,
        extraButtons: null,
        hideOptions: {},
        disabled: false,
    };

    render() {
        const {
            equipmentTypes, features: availableFeatures, buildings,
            extraButtons, hideOptions, disabled, showOnlyAuthorizedFilter, hasOwnedRooms,
            filters: {
                capacity, onlyFavorites, onlyMine, onlyAuthorized, equipment, features, building,
                ...extraFilters
            },
            actions: {setFilterParameter, setFilters}
        } = this.props;
        const hideShowOnlyForm = hideOptions.favorites && !hasOwnedRooms && !onlyMine && !showOnlyAuthorizedFilter;
        const equipmentFilter = (!!equipmentTypes.length || !!availableFeatures.length) && (
            <FilterDropdownFactory name="equipment"
                                   title={<Translate>Equipment</Translate>}
                                   form={(values, setParentField) => (
                                       <EquipmentForm setParentField={setParentField}
                                                      selectedEquipment={values.equipment}
                                                      selectedFeatures={values.features}
                                                      availableEquipment={equipmentTypes}
                                                      availableFeatures={availableFeatures} />
                                   )}
                                   counter
                                   setGlobalState={setFilters}
                                   initialValues={{equipment, features}}
                                   renderValue={renderEquipment}
                                   disabled={disabled} />
        );

        return (
            <Button.Group size="small">
                <Button icon="filter" as="div" disabled />
                <FilterBarController>
                    {!hideOptions.building && (
                        <FilterDropdownFactory name="building"
                                               title={<Translate>Building</Translate>}
                                               form={({building: selectedBuilding}, setParentField) => (
                                                   <BuildingForm setParentField={setParentField}
                                                                 buildings={buildings}
                                                                 building={selectedBuilding} />
                                               )}
                                               setGlobalState={data => setFilterParameter('building', data.building)}
                                               initialValues={{building}}
                                               renderValue={renderBuilding}
                                               disabled={disabled} />
                    )}
                    {!hideOptions.capacity && (
                        <FilterDropdownFactory name="capacity"
                                               title={<Translate>Min. Capacity</Translate>}
                                               form={({capacity: selectedCapacity}, setParentField) => (
                                                   <CapacityForm setParentField={setParentField}
                                                                 capacity={selectedCapacity} />
                                               )}
                                               setGlobalState={data => setFilterParameter('capacity', data.capacity)}
                                               initialValues={{capacity}}
                                               renderValue={renderCapacity}
                                               disabled={disabled} />
                    )}
                    {!hideOptions.equipment && equipmentFilter}
                    <Overridable id="RoomFilterBar.extraFilters"
                                 setFilter={setFilterParameter}
                                 filters={extraFilters} />
                    {!hideShowOnlyForm && (
                        <FilterDropdownFactory name="room-different"
                                               title={<Translate>Show only...</Translate>}
                                               form={(data, setParentField) => (
                                                   <ShowOnlyForm {...data}
                                                                 setParentField={setParentField}
                                                                 showOnlyAuthorizedFilter={showOnlyAuthorizedFilter}
                                                                 hideFavoritesFilter={hideOptions.favorites}
                                                                 disabled={disabled} />
                                               )}
                                               setGlobalState={setFilters}
                                               renderValue={(data) => {
                                                   const iconMap = {
                                                       onlyFavorites: 'star',
                                                       onlyMine: 'user',
                                                       onlyAuthorized: 'lock open'
                                                   };
                                                   const icons = Object.entries(iconMap)
                                                       .filter(([key]) => data[key])
                                                       .map(([key, icon]) => <Icon key={key} name={icon} />);
                                                   return icons.length !== 0 ? icons : null;
                                               }}
                                               initialValues={{onlyFavorites, onlyMine, onlyAuthorized}}
                                               disabled={disabled} />

                    )}
                    {extraButtons}
                </FilterBarController>
            </Button.Group>
        );
    }
}

export default (namespace, searchRoomsSelectors) => connect(
    state => ({
        filters: searchRoomsSelectors.getFilters(state),
        equipmentTypes: roomsSelectors.getEquipmentTypeNamesWithoutFeatures(state),
        features: roomsSelectors.getFeatures(state),
        buildings: roomsSelectors.getBuildings(state),
        hasOwnedRooms: userSelectors.hasOwnedRooms(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            setFilterParameter: (param, value) => filtersActions.setFilterParameter(namespace, param, value),
            setFilters: (params) => filtersActions.setFilters(namespace, params),
        }, dispatch)
    })
)(Overridable.component('RoomFilterBar', RoomFilterBarBase));
