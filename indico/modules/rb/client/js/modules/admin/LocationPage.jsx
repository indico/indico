// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import createDecorator from 'final-form-calculate';
import {Field} from 'react-final-form';
import {List} from 'semantic-ui-react';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {formatters, validators as v, parsers as p, ReduxDropdownField, ReduxFormField} from 'indico/react/forms';
import {snakifyKeys} from 'indico/utils/case';
import * as adminActions from './actions';
import * as adminSelectors from './selectors';
import EditableList from './EditableList';

import './EditableList.module.scss';


const MAP_TEMPLATE_OPTIONS = [{
    value: 'none',
    text: Translate.string('None'),
}, {
    value: 'custom',
    text: Translate.string('Custom'),
}, {
    value: 'https://www.google.com/maps/place/{lat},{lng}',
    text: 'Google Maps',
}, {
    value: 'https://www.openstreetmap.org/?mlat={lat}&mlon={lng}&zoom=18',
    text: 'OpenStreetMap',
}];

const formDecorator = createDecorator({
    field: '_map_url_template_choice',
    updates: (value) => {
        if (value !== 'custom') {
            return {map_url_template: value === 'none' ? null : value};
        }
        return {};
    }
});


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

    renderItem = ({name, numRooms}) => (
        <List.Content styleName="info">
            <List.Header>
                <span styleName="name">{name}</span>
            </List.Header>
            <List.Description>
                {!numRooms ? (
                    <Translate>No rooms</Translate>
                ) : (
                    <PluralTranslate count={numRooms}>
                        <Singular>
                            <Param name="count" wrapper={<strong />}>1</Param> room
                        </Singular>
                        <Plural>
                            <Param name="count" wrapper={<strong />} value={numRooms} />
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
            <Field name="_map_url_template_choice" component={ReduxDropdownField}
                   parse={null}
                   label={Translate.string('Map URL template')}
                   selection options={MAP_TEMPLATE_OPTIONS}>
                <p className="field-description">
                    <Translate>
                        Indico can show a link to an external map when a room is associated to an event.
                    </Translate>
                </p>
            </Field>
            <Field name="_map_url_template_choice" subscription={{value: true}}>
                {({input: {value: selectedTemplate}}) => (
                    <Field name="map_url_template" component={ReduxFormField} as="input"
                           format={formatters.trim} formatOnBlur
                           readOnly={selectedTemplate !== 'custom'}
                           style={selectedTemplate === 'none' ? {display: 'none'} : {}}
                           parse={p.nullIfEmpty}
                           validate={v.optional(v.url)}>
                        {selectedTemplate === 'custom' && (
                            <p className="field-description">
                                <Translate>
                                    Specify a custom URL template using any of the following placeholders:
                                    {' '}
                                    <Param name="placeholders" wrapper={<code />}
                                           value="{id}, {building}, {floor}, {number}, {lat}, {lng}" />
                                </Translate>
                            </p>
                        )}
                    </Field>
                )}
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

    getInitialEditValues = (loc) => {
        loc = _.pick(snakifyKeys(loc), ['name', 'room_name_format', 'map_url_template', '_map_url_template_choice']);
        if (!loc.map_url_template) {
            loc.map_url_template = null;
            loc._map_url_template_choice = 'none';
        } else {
            const template = MAP_TEMPLATE_OPTIONS.find(x => x.value === loc.map_url_template);
            loc._map_url_template_choice = template ? template.value : 'custom';
        }
        return loc;
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
                          initialEditValues={this.getInitialEditValues}
                          initialAddValues={{
                              room_name_format: '{building}/{floor}-{number}',
                              _map_url_template_choice: 'none',
                              map_url_template: null,
                          }}
                          addFormProps={{decorators: [formDecorator]}}
                          editFormProps={{decorators: [formDecorator]}}
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
