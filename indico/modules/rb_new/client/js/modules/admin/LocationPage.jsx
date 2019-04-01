/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Field} from 'react-final-form';
import {List} from 'semantic-ui-react';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {formatters, validators as v, ReduxFormField} from 'indico/react/forms';
import {snakifyKeys} from 'indico/utils/case';
import * as adminActions from './actions';
import * as adminSelectors from './selectors';
import EditableList from './EditableList';

import './EditableList.module.scss';


class LocationPage extends React.PureComponent {
    static propTypes = {
        locations: PropTypes.array.isRequired,
        isFetching: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
            deleteLocation: PropTypes.func.isRequired,
            updateLocation: PropTypes.func.isRequired,
            createLocation: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {isFetching, actions: {fetchLocations}} = this.props;
        if (!isFetching) {
            fetchLocations();
        }
    }

    renderItem = ({name, rooms}) => (
        <List.Content styleName="info">
            <List.Header>
                <span styleName="name">{name}</span>
            </List.Header>
            <List.Description>
                {!rooms.length ? (
                    <Translate>No rooms</Translate>
                ) : (
                    <PluralTranslate count={rooms.length}>
                        <Singular>
                            <Param name="count" wrapper={<strong />}>1</Param> room
                        </Singular>
                        <Plural>
                            <Param name="count" wrapper={<strong />} value={rooms.length} />
                            {' '}
                            rooms
                        </Plural>
                    </PluralTranslate>
                )}
            </List.Description>
        </List.Content>
    );

    renderForm = () => (
        <>
            <Field name="name" component={ReduxFormField} as="input"
                   required
                   format={formatters.trim} formatOnBlur
                   label={Translate.string('Name')}
                   autoFocus />
            <Field name="room_name_format" component={ReduxFormField} as="input"
                   required
                   format={formatters.trim} formatOnBlur
                   label={Translate.string('Room name format')}
                   validate={val => {
                       const rv = v.required(val);
                       if (rv) {
                           return rv;
                       }
                       const missing = ['{building}', '{floor}', '{number}'].filter(x => !val.includes(x));
                       if (missing.length) {
                           return PluralTranslate.string(
                               'Missing placeholder: {placeholders}',
                               'Missing placeholders: {placeholders}',
                               missing.length,
                               {placeholders: missing.join(', ')}
                           );
                       }
                   }} />
            <Field name="map_url_template" component={ReduxFormField} as="input"
                   format={formatters.trim} formatOnBlur
                   label={Translate.string('Map URL template')}
                   validate={val => {
                       if (val && !val.match(/https?:\/\/.+/)) {
                           return Translate.string('Please provide a valid URL');
                       }
                   }}>
                <p className="field-description">
                    <Translate>
                        Indico can show a link to an external map when a room is associated to an event.
                        Specify the template to generate those links, using any of the following placeholders:
                        {' '}
                        <Param name="placeholders" wrapper={<code />}
                               value="{id}, {building}, {floor}, {number}, {lat}, {lng}" />
                    </Translate>
                </p>
            </Field>
        </>
    );

    renderDeleteMessage = ({name}) => {
        return (
            <Translate>
                Are you sure you want to delete the location
                {' '}
                <Param name="name" wrapper={<strong />} value={name} />
                {' '}
                and all data associated with it?
            </Translate>
        );
    };


    render() {
        const {
            isFetching, locations,
            actions: {createLocation, updateLocation, deleteLocation},
        } = this.props;

        return (
            <EditableList title={Translate.string('Locations')}
                          addModalTitle={Translate.string('Add location')}
                          isFetching={isFetching}
                          items={locations}
                          initialEditValues={snakifyKeys}
                          initialAddValues={{
                              room_name_format: '{building}/{floor}-{number}',
                              map_url_template: 'https://www.google.com/maps/place/{lat},{lng}',
                          }}
                          renderItem={this.renderItem}
                          canDeleteItem={loc => loc.canDelete}
                          renderAddForm={this.renderForm}
                          renderEditForm={this.renderForm}
                          renderDeleteMessage={this.renderDeleteMessage}
                          onCreate={createLocation}
                          onUpdate={updateLocation}
                          onDelete={deleteLocation} />
        );
    }
}

export default connect(
    state => ({
        locations: adminSelectors.getAllLocations(state),
        isFetching: adminSelectors.isFetchingLocations(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
            deleteLocation: ({id}) => adminActions.deleteLocation(id),
            updateLocation: ({id}, data) => adminActions.updateLocation(id, data),
            createLocation: adminActions.createLocation,
        }, dispatch),
    })
)(LocationPage);
