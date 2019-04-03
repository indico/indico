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
import {Form as FinalForm} from 'react-final-form';
import {Button, Confirm, Form, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {getChangedValues} from 'indico/react/forms';

import './EditableList.module.scss';


/**
 * A list item component that supports inline editing and deletion.
 */
export default class EditableListItem extends React.PureComponent {
    static propTypes = {
        item: PropTypes.object.isRequired,
        canDelete: PropTypes.func,
        renderDisplay: PropTypes.func.isRequired,
        renderEditForm: PropTypes.func.isRequired,
        confirmDeleteMessage: PropTypes.any.isRequired,
        initialEditValues: PropTypes.func,
        onDelete: PropTypes.func.isRequired,
        onUpdate: PropTypes.func.isRequired,
    };

    static defaultProps = {
        canDelete: () => true,
        initialEditValues: item => item,
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

    confirmDelete = async () => {
        const {item, onDelete} = this.props;
        this.setState({deleting: true, confirming: false});
        const rv = await onDelete(item);
        if (rv.error) {
            // we could show the error but unless client-side validation
            // failed or didn't work because of parallel changes, we should
            // never end up here, so not worth doing this for now!
            this.setState({deleting: false});
        }
    };

    handleEditClick = () => {
        const {editing} = this.state;
        this.setState({editing: !editing});
    };

    handleSubmit = async (data, form) => {
        const {item, onUpdate} = this.props;
        this.setState({saving: true});
        const rv = await onUpdate(item, getChangedValues(data, form));
        if (rv.error) {
            this.setState({saving: false});
            return rv.error;
        }
        this.setState({saving: false, editing: false});
    };

    render() {
        const {confirming, editing, deleting, saving} = this.state;
        const {confirmDeleteMessage, renderDisplay, renderEditForm, initialEditValues, item, canDelete} = this.props;

        return (
            <List.Item>
                <div styleName={editing ? 'item editing' : 'item'}>
                    {editing ? (
                        <FinalForm onSubmit={this.handleSubmit}
                                   initialValues={initialEditValues(item)}
                                   initialValuesEqual={_.isEqual}
                                   subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
                            {fprops => (
                                <Form onSubmit={fprops.handleSubmit}>
                                    {renderEditForm(fprops)}
                                    <Form.Group>
                                        <Form.Button type="submit"
                                                     disabled={(
                                                         fprops.hasValidationErrors ||
                                                         fprops.pristine ||
                                                         fprops.submitting
                                                     )}
                                                     loading={fprops.submitting}
                                                     primary
                                                     content={Translate.string('Save')} />
                                    </Form.Group>
                                </Form>
                            )}
                        </FinalForm>
                    ) : (
                        renderDisplay(item)
                    )}
                    <List.Content styleName="actions">
                        <Button icon="pencil" basic onClick={this.handleEditClick}
                                disabled={saving || deleting} primary={editing} />
                        <Button icon="trash" basic negative onClick={this.handleDeleteClick}
                                loading={deleting} disabled={saving || deleting || !canDelete(item)} />
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
