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
import {Icon, Popup} from 'semantic-ui-react';


export default function RoomFeatureEntry({feature, color, size}) {
    const {icon, title, equipment} = feature;
    const trigger = <Icon name={icon} color={color} size={size} />;
    if (equipment.length === 1 && equipment[0] === title) {
        return <Popup trigger={trigger} content={title} />;
    }
    return (
        <Popup trigger={trigger}>
            {title} ({equipment.filter(eq => eq !== title).join(', ')})
        </Popup>
    );
}

RoomFeatureEntry.propTypes = {
    feature: PropTypes.shape({
        icon: PropTypes.string.isRequired,
        title: PropTypes.string.isRequired,
        equipment: PropTypes.arrayOf(PropTypes.string).isRequired,
    }).isRequired,
    color: PropTypes.string.isRequired,
    size: PropTypes.string
};

RoomFeatureEntry.defaultProps = {
    size: undefined
};
