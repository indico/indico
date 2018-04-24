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
import {Button, Icon} from 'semantic-ui-react';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import FilterDropdown from './filters/FilterDropdown';
import CapacityForm from './filters/CapacityForm';


const capacityRenderer = ({capacity}) => (
    (capacity === null)
        ? null : (
            <span>
                <Icon name="user" />
                {capacity}
            </span>
        ));

export default function RoomFilterBar({capacity, children, setFilterParameter}) {
    return (
        <Button.Group>
            {children}
            <FilterDropdown title={<Translate>Min. Capacity</Translate>}
                            form={(ref, fieldValues, setParentField) => (
                                <CapacityForm ref={ref}
                                              setParentField={setParentField}
                                              capacity={fieldValues.capacity} />
                            )}
                            setGlobalState={data => setFilterParameter('capacity', data.capacity)}
                            initialValues={{capacity}}
                            renderValue={capacityRenderer} />
        </Button.Group>
    );
}

RoomFilterBar.propTypes = {
    capacity: propTypes.number,
    setFilterParameter: propTypes.func.isRequired,
    children: propTypes.node
};

RoomFilterBar.defaultProps = {
    capacity: null,
    children: null
};
