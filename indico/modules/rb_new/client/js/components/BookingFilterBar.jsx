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
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';
import RoomFilterBar, {equipmentType} from './RoomFilterBar';

import FilterDropdown from './filters/FilterDropdown';
import RecurrenceForm from './filters/RecurrenceForm';
import DateForm from './filters/DateForm';
import TimeForm from './filters/TimeForm';

import recurrenceRenderer from './filters/RecurrenceRenderer';
import dateRenderer from './filters/DateRenderer';
import timeRenderer from './filters/TimeRenderer';


export default function FilterBar({
    recurrence, dates, timeSlot, capacity, onlyFavorites, onlyMine, equipment, setFilterParameter, equipmentTypes,
    hasOwnedRooms, hasFavoriteRooms
}) {
    return (
        <RoomFilterBar capacity={capacity}
                       onlyFavorites={onlyFavorites}
                       onlyMine={onlyMine}
                       equipment={equipment}
                       setFilterParameter={setFilterParameter}
                       equipmentTypes={equipmentTypes}
                       hasOwnedRooms={hasOwnedRooms}
                       hasFavoriteRooms={hasFavoriteRooms}>
            <FilterDropdown title={<Translate>Recurrence</Translate>}
                            form={(fieldValues, setParentField) => (
                                <RecurrenceForm setParentField={setParentField} {...fieldValues} />
                            )}
                            setGlobalState={({type, number, interval}) => {
                                setFilterParameter('recurrence', {type, number, interval});
                            }}
                            initialValues={recurrence}
                            defaults={{
                                type: 'single',
                                number: 1,
                                interval: 'week'
                            }}
                            renderValue={recurrenceRenderer} />
            <FilterDropdown title={<Translate>Date</Translate>}
                            form={(fieldValues, setParentField, handleOK) => (
                                <DateForm setParentField={setParentField}
                                          isRange={recurrence.type !== 'single'}
                                          handleOK={handleOK}
                                          {...dates} />
                            )}
                            setGlobalState={setFilterParameter.bind(undefined, 'dates')}
                            initialValues={dates}
                            renderValue={dateRenderer}
                            showButtons={false} />
            <FilterDropdown title={<Translate>Time</Translate>}
                            form={(fieldValues, setParentField) => (
                                <TimeForm setParentField={setParentField}
                                          {...fieldValues} />
                            )}
                            setGlobalState={setFilterParameter.bind(undefined, 'timeSlot')}
                            initialValues={timeSlot}
                            renderValue={timeRenderer} />
        </RoomFilterBar>
    );
}


FilterBar.propTypes = {
    equipmentTypes: propTypes.arrayOf(propTypes.string).isRequired,
    recurrence: propTypes.shape({
        number: propTypes.number,
        type: propTypes.string,
        interval: propTypes.string
    }).isRequired,
    dates: propTypes.shape({
        startDate: propTypes.string,
        endDate: propTypes.string
    }).isRequired,
    timeSlot: propTypes.shape({
        startTime: propTypes.string,
        endTime: propTypes.string
    }).isRequired,
    capacity: propTypes.number,
    onlyFavorites: propTypes.bool,
    onlyMine: propTypes.bool,
    equipment: equipmentType,
    setFilterParameter: propTypes.func.isRequired,
    hasOwnedRooms: propTypes.bool,
    hasFavoriteRooms: propTypes.bool,
};

FilterBar.defaultProps = {
    capacity: null,
    onlyFavorites: null,
    onlyMine: null,
    equipment: [],
    hasOwnedRooms: false,
    hasFavoriteRooms: false,
};
