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
    if (Object.values(equipment).some(v => v)) {
        return (
            <>
                <Translate>Equipment</Translate>
                <Label circular horizontal className="white" size="medium" styleName="filter-bar-button-label">
                    {Object.values(equipment).filter(v => v).length}
                </Label>
            </>
        );
    } else {
        return null;
    }
};

export default function RoomFilterBar(
    {
        capacity, onlyFavorites, onlyMine, children, equipment, setFilterParameter, equipmentTypes,
        hasOwnedRooms, hasFavoriteRooms
    }
) {
    const equipmentFilter = !!equipmentTypes.length && (
        <FilterDropdown title={<Translate>Equipment</Translate>}
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
            {children}
            <FilterDropdown title={<Translate>Min. Capacity</Translate>}
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
            <Popup trigger={<Button icon="star" primary={onlyFavorites} disabled={!onlyFavorites && !hasFavoriteRooms}
                                    onClick={() => setFilterParameter('onlyFavorites', !onlyFavorites)} />}
                   content={Translate.string('Show only my favorite rooms')} />
        </Button.Group>
    );
}

export const equipmentType = PropTypes.object;

RoomFilterBar.propTypes = {
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

RoomFilterBar.defaultProps = {
    capacity: null,
    onlyFavorites: false,
    onlyMine: false,
    hasFavoriteRooms: false,
    hasOwnedRooms: false,
    children: null,
    equipment: [],
};
