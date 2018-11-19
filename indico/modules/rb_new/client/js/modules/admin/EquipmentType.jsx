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

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Field, Form as FinalForm} from 'react-final-form';
import {Button, Confirm, Form, Icon, List, Popup} from 'semantic-ui-react';
import {formatters, ReduxDropdownField, ReduxFormField} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import './EquipmentTypesPage.module.scss';


export default class EquipmentType extends React.PureComponent {
    static propTypes = {
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
        features: PropTypes.array.isRequired,
        numRooms: PropTypes.number.isRequired,
        availableFeatures: PropTypes.array.isRequired,
        deleteEquipmentType: PropTypes.func,
        updateEquipmentType: PropTypes.func,
    };

    static defaultProps = {
        deleteEquipmentType: null,
        updateEquipmentType: null,
    };

    state = {
        // delete
        confirming: false,
        deleting: false,
        // edit
        editing: false,
        saving: false,
    };

    handleDeleteClick = () => {
        this.setState({confirming: true, editing: false});
    };

    cancelDelete = () => {
        this.setState({confirming: false});
    };

    confirmDelete = () => {
        const {id, deleteEquipmentType} = this.props;
        this.setState({deleting: true, confirming: false});
        deleteEquipmentType(id);
    };

    handleEditClick = () => {
        const {editing} = this.state;
        this.setState({editing: !editing});
    };

    handleSubmit = async (data) => {
        const {id, updateEquipmentType} = this.props;
        this.setState({saving: true});
        const rv = await updateEquipmentType(id, data);
        if (rv.error) {
            this.setState({saving: false});
            return rv.error;
        }
        this.setState({saving: false, editing: false});
    };

    render() {
        const {confirming, editing, deleting, saving} = this.state;
        const {name, numRooms, features, availableFeatures} = this.props;

        const confirmDeleteMessage = (
            <>
                <Translate>
                    Are you sure you want to delete the equipment type
                    {' '}
                    <Param name="name" wrapper={<strong />} value={name} />?
                </Translate>
                {numRooms > 0 && (
                    <>
                        <br />
                        <PluralTranslate count={numRooms}>
                            <Singular>
                                It is currently used by <Param name="count" wrapper={<strong />}>one</Param> room.
                            </Singular>
                            <Plural>
                                It is currently used by
                                {' '}
                                <Param name="count" wrapper={<strong />} value={numRooms} /> rooms.
                            </Plural>
                        </PluralTranslate>
                    </>
                )}
            </>
        );

        const featureOptions = availableFeatures.map(feat => ({
            key: feat.name,
            value: feat.name,
            text: feat.title,
            icon: feat.icon,
        }));

        return (
            <List.Item>
                <div styleName="item">
                    {editing ? (
                        <FinalForm onSubmit={this.handleSubmit}
                                   initialValues={{name, features: features.map(x => x.name)}}
                                   initialValuesEqual={_.isEqual}
                                   subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
                            {(fprops) => (
                                <Form onSubmit={fprops.handleSubmit}>
                                    <Form.Group widths="equal">
                                        <Field name="name" component={ReduxFormField} as="input"
                                               format={formatters.trim} formatOnBlur
                                               placeholder={Translate.string('Name')}
                                               disabled={fprops.submitting} />
                                        <Field name="features" component={ReduxDropdownField}
                                               multiple selection options={featureOptions}
                                               placeholder={Translate.string('Features')}
                                               disabled={fprops.submitting} />
                                    </Form.Group>
                                    <Form.Group>
                                        <Form.Button type="submit"
                                                     disabled={(
                                                         fprops.hasValidationErrors ||
                                                         fprops.pristine ||
                                                         fprops.submitting
                                                     )}
                                                     loading={fprops.submitting} primary
                                                     content={Translate.string('Save')} />
                                    </Form.Group>
                                </Form>
                            )}
                        </FinalForm>
                    ) : (
                        <>
                            <List.Content styleName="info">
                                <List.Header>
                                    <span styleName="name">{name}</span>
                                    {features.map(feat => (
                                        <Popup key={feat.name}
                                               trigger={<Icon name={feat.icon || 'cog'} color="blue" />}>
                                            <Translate>
                                                This equipment type provides the
                                                {' '}
                                                <Param name="name" wrapper={<strong />} value={feat.title} /> feature.
                                            </Translate>
                                        </Popup>
                                    ))}
                                </List.Header>
                                <List.Description>
                                    {!numRooms ? (
                                        <Translate>Currently unused</Translate>
                                    ) : (
                                        <PluralTranslate count={numRooms}>
                                            <Singular>
                                                Available in <Param name="count" wrapper={<strong />}>1</Param> room
                                            </Singular>
                                            <Plural>
                                                Available in
                                                {' '}
                                                <Param name="count" wrapper={<strong />} value={numRooms} />
                                                {' '}
                                                rooms
                                            </Plural>
                                        </PluralTranslate>
                                    )}
                                </List.Description>
                            </List.Content>
                        </>
                    )}
                    <List.Content styleName="actions">
                        <Button icon="pencil" basic onClick={this.handleEditClick}
                                disabled={saving || deleting} primary={editing} />
                        <Button icon="trash" basic negative onClick={this.handleDeleteClick}
                                loading={deleting} disabled={saving || deleting} />
                        <Confirm header={Translate.string('Confirm deletion')}
                                 content={{content: confirmDeleteMessage}}
                                 confirmButton={<Button content={Translate.string('Delete')} negative />}
                                 cancelButton={Translate.string('Cancel')}
                                 open={confirming}
                                 onCancel={this.cancelDelete}
                                 onConfirm={this.confirmDelete} />
                    </List.Content>
                </div>
            </List.Item>
        );
    }
}
