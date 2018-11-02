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
import {Grid, Header, Icon, Popup} from 'semantic-ui-react';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {formatLatLon} from '../common/map/util';

import RoomFeatureEntry from './RoomFeatureEntry';
import SpriteImage from './SpriteImage';

import styles from './RoomBasicDetails.module.scss';


function RoomFeaturesBox({room: {features}}) {
    if (!features.length) {
        return null;
    }
    return (
        <div styleName="feature-box">
            <div styleName="feature-entries">
                {features.map(feature => (
                    <RoomFeatureEntry key={feature.name}
                                      feature={feature}
                                      color="teal"
                                      size="large"
                                      classes={styles['feature-entry']} />
                ))}
            </div>
        </div>
    );
}

RoomFeaturesBox.propTypes = {
    room: PropTypes.shape({
        features: PropTypes.array.isRequired,
    }).isRequired,
};

function AnnotatedIcon({name, text}) {
    return (
        <Popup content={text}
               trigger={<Icon name={name} />} />

    );
}

AnnotatedIcon.propTypes = {
    name: PropTypes.string.isRequired,
    text: PropTypes.string.isRequired
};

export default function RoomBasicDetails({room}) {
    const {
        ownerName: owner, latitude, longitude, division, locationName: location, surfaceArea: surface, capacity,
        telephone, fullName: name
    } = room;
    return (
        <Grid columns={2}>
            <Grid.Column textAlign="center" styleName="photo-column">
                <div styleName="image-container">
                    <SpriteImage pos={room.spritePosition}
                                 height="100%"
                                 width="100%"
                                 fillVertical />
                    <RoomFeaturesBox room={room} />
                </div>
            </Grid.Column>
            <Grid.Column styleName="data-column">
                <Header>
                    {name}
                    <Header.Subheader>{division}</Header.Subheader>
                </Header>
                <ul styleName="room-basic-details">
                    <li>{location}</li>
                    <li className="has-icon">
                        <AnnotatedIcon name="id badge outline"
                                       text={Translate.string('Room Owner')} />
                        {owner}
                    </li>
                    <li className="has-icon">
                        {telephone && (
                            <>
                                <AnnotatedIcon name="phone"
                                               text={Translate.string('Phone number')} />
                                {room.telephone}
                            </>
                        )}
                    </li>
                    <li className="has-icon">
                        {capacity && (
                            <>
                                <AnnotatedIcon name="users" text={Translate.string('Capacity')} />
                                <PluralTranslate count={capacity}>
                                    <Singular>
                                        1 <Param name="label" wrapper={<label />}>seat</Param>
                                    </Singular>
                                    <Plural>
                                        <Param name="count" value={capacity} />
                                        {' '}
                                        <Param name="label" wrapper={<label />}>seats</Param>
                                    </Plural>
                                </PluralTranslate>
                            </>
                        )}
                    </li>
                    <li className="has-icon">
                        {surface && (
                            <>
                                <AnnotatedIcon name="cube" text={Translate.string('Surface Area')} />
                                {surface} <label>m²</label>
                            </>
                        )}
                    </li>
                    <li className="has-icon">
                        {latitude && (
                            <>
                                <AnnotatedIcon name="location arrow" text={Translate.string('Geographical Coordinates')} />
                                {formatLatLon(latitude, longitude)}
                            </>
                        )}
                    </li>
                </ul>
            </Grid.Column>
        </Grid>
    );
}

RoomBasicDetails.propTypes = {
    room: PropTypes.object.isRequired
};
