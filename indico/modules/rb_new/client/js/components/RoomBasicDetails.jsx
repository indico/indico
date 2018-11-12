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
import {Grid, Header, Icon} from 'semantic-ui-react';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import RoomFeatureEntry from './RoomFeatureEntry';
import SpriteImage from './SpriteImage';

import './RoomBasicDetails.module.scss';


function RoomFeaturesBox({room: {features}}) {
    if (!features.length) {
        return null;
    }
    return (
        <div styleName="equipment-box">
            {features.map(feature => (
                <RoomFeatureEntry key={feature.name} feature={feature} color="teal" size="large" />
            ))}
        </div>
    );
}

RoomFeaturesBox.propTypes = {
    room: PropTypes.shape({
        features: PropTypes.array.isRequired,
    }).isRequired,
};

export default function RoomBasicDetails({room}) {
    const {
        ownerName: owner, latitude, longitude, division, locationName: location, surfaceArea: surface, capacity,
        telephone, fullName: name
    } = room;
    return (
        <Grid columns={2}>
            <Grid.Column textAlign="center">
                <SpriteImage pos={room.sprite_position}
                             origin="0" />
                <RoomFeaturesBox room={room} />
            </Grid.Column>
            <Grid.Column>
                <Header>
                    {name}
                    <Header.Subheader>{division}</Header.Subheader>
                </Header>
                <div>{location}</div>
                {owner && (<><Translate>Owner</Translate>: {owner}</>)}
                {latitude && (
                    <div>
                        <Icon name="location arrow" /> {latitude}, {longitude}
                    </div>
                )}
                {telephone && <div><Icon name="phone" /> {room.telephone}</div>}
                {capacity && (
                    <div>
                        <PluralTranslate count={capacity}>
                            <Singular>
                                1 seat
                            </Singular>
                            <Plural>
                                <Param name="count" value={capacity} /> seats
                            </Plural>
                        </PluralTranslate>
                    </div>
                )}
                {surface && <div>{surface}m²</div>}
            </Grid.Column>
        </Grid>
    );
}

RoomBasicDetails.propTypes = {
    room: PropTypes.object.isRequired
};
