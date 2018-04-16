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
import {Button} from 'antd';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import FilterDropdown from './filters/FilterDropdown';
import RecurrenceForm from './filters/RecurrenceForm';
import DateForm from './filters/DateForm';
import recurrenceRenderer from './filters/RecurrenceRenderer';
import dateRenderer from './filters/DateRenderer';


export default function FilterBar({recurrence, dates, setFilterParameter}) {
    return (
        <Button.Group size="medium">
            <FilterDropdown title={<Translate>Recurrence</Translate>}
                            form={(ref, setParentField) => (
                                <RecurrenceForm ref={ref} setParentField={setParentField} {...recurrence} />
                            )}
                            setGlobalState={setFilterParameter.bind(undefined, 'recurrence')}
                            initialValues={recurrence}
                            displayValue={recurrenceRenderer} />
            <FilterDropdown title={<Translate>Date</Translate>}
                            form={(ref, setParentField) => (
                                <DateForm ref={ref}
                                          setParentField={setParentField}
                                          isRange={recurrence.type !== 'single'}
                                          {...dates} />
                            )}
                            setGlobalState={setFilterParameter.bind(undefined, 'dates')}
                            initialValues={dates}
                            displayValue={dateRenderer} />
        </Button.Group>
    );
}

FilterBar.propTypes = {
    recurrence: propTypes.shape({
        number: propTypes.number,
        type: propTypes.string,
        interval: propTypes.string
    }).isRequired,
    dates: propTypes.shape({
        startDate: propTypes.string,
        endDate: propTypes.string
    }).isRequired,
    setFilterParameter: propTypes.func.isRequired
};
