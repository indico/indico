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
import {Button, Form, Header, List, Modal, Placeholder} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import EditableListItem from './EditableListItem';

import './EditableList.module.scss';


class AddItemModal extends React.PureComponent {
    static propTypes = {
        title: PropTypes.string.isRequired,
        initialValues: PropTypes.object.isRequired,
        renderForm: PropTypes.func.isRequired,
        onClose: PropTypes.func.isRequired,
        onSubmit: PropTypes.func.isRequired,
    };

    handleSubmit = async (data) => {
        const {onSubmit} = this.props;
        const rv = await onSubmit(data);
        if (rv.error) {
            return rv.error;
        }
    };

    render() {
        const {title, initialValues, onClose, renderForm} = this.props;

        return (
            <Modal open size="mini" closeIcon onClose={onClose}>
                <Modal.Header>
                    {title}
                </Modal.Header>
                <Modal.Content>
                    <FinalForm onSubmit={this.handleSubmit}
                               initialValues={initialValues}
                               initialValuesEqual={_.isEqual}
                               subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
                        {fprops => (
                            <Form onSubmit={fprops.handleSubmit}>
                                {renderForm(fprops)}
                                <Form.Button type="submit"
                                             disabled={(
                                                 fprops.hasValidationErrors ||
                                                 fprops.pristine ||
                                                 fprops.submitting
                                             )}
                                             loading={fprops.submitting}
                                             primary
                                             content={Translate.string('Add')} />
                            </Form>
                        )}
                    </FinalForm>
                </Modal.Content>
            </Modal>
        );
    }
}

/**
 * A list component that supports adding, removing, and inline editing.
 */
export default class EditableList extends React.PureComponent {
    static propTypes = {
        title: PropTypes.string.isRequired,
        addModalTitle: PropTypes.string.isRequired,
        isFetching: PropTypes.bool.isRequired,
        items: PropTypes.array.isRequired,
        initialAddValues: PropTypes.object,
        initialEditValues: PropTypes.func,
        renderItem: PropTypes.func.isRequired,
        canDeleteItem: PropTypes.func,
        renderAddForm: PropTypes.func.isRequired,
        renderEditForm: PropTypes.func.isRequired,
        renderDeleteMessage: PropTypes.func.isRequired,
        onDelete: PropTypes.func.isRequired,
        onUpdate: PropTypes.func.isRequired,
        onCreate: PropTypes.func.isRequired,
    };

    static defaultProps = {
        initialAddValues: {},
        initialEditValues: undefined,
        canDeleteItem: undefined,
    };

    state = {
        adding: false,
    };

    handleAddClick = () => {
        this.setState({adding: true});
    };

    handleAddClose = () => {
        this.setState({adding: false});
    };

    handleCreate = async (data) => {
        const {onCreate} = this.props;
        const rv = await onCreate(data);
        if (!rv.error) {
            this.setState({adding: false});
        }
        return rv;
    };

    render() {
        const {
            title, addModalTitle, renderAddForm, renderEditForm, renderDeleteMessage, renderItem, initialEditValues,
            initialAddValues, canDeleteItem, isFetching, items, onDelete, onUpdate,
        } = this.props;
        const {adding} = this.state;

        return (
            <>
                <Header as="h2" styleName="header">
                    {title}
                    <Button size="small" content={Translate.string('Add')} onClick={this.handleAddClick} />
                </Header>
                {isFetching ? (
                    <Placeholder fluid>
                        {_.range(20).map(i => (
                            <Placeholder.Line key={i} length="full" />
                        ))}
                    </Placeholder>
                ) : (
                    <>
                        <List divided relaxed>
                            {items.map(item => (
                                <EditableListItem key={item.id}
                                                  item={item}
                                                  onDelete={onDelete}
                                                  onUpdate={onUpdate}
                                                  canDelete={canDeleteItem}
                                                  renderDisplay={renderItem}
                                                  renderAddForm={renderEditForm}
                                                  renderEditForm={renderEditForm}
                                                  initialEditValues={initialEditValues}
                                                  confirmDeleteMessage={renderDeleteMessage(item)} />
                            ))}
                        </List>
                        {adding && (
                            <AddItemModal onSubmit={this.handleCreate}
                                          onClose={this.handleAddClose}
                                          title={addModalTitle}
                                          renderForm={renderAddForm}
                                          initialValues={initialAddValues} />
                        )}
                    </>
                )}
            </>
        );
    }
}
