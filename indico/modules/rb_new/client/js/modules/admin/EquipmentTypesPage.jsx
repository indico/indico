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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Field, Form as FinalForm} from 'react-final-form';
import {Button, Form, Header, List, Modal, Placeholder} from 'semantic-ui-react';
import {formatters, ReduxDropdownField, ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import * as adminActions from './actions';
import * as adminSelectors from './selectors';
import EquipmentType from './EquipmentType';

import './EquipmentTypesPage.module.scss';


class AddEquipmentTypeModal extends React.PureComponent {
    static propTypes = {
        features: PropTypes.array.isRequired,
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
        const {features, onClose} = this.props;

        const featureOptions = features.map(feat => ({
            key: feat.name,
            value: feat.name,
            text: feat.title,
            icon: feat.icon,
        }));

        return (
            <Modal open size="mini" closeIcon onClose={onClose}>
                <Modal.Header>
                    <Translate>
                        Add equipment type
                    </Translate>
                </Modal.Header>
                <Modal.Content>
                    <FinalForm onSubmit={this.handleSubmit}
                               initialValues={{features: []}}
                               initialValuesEqual={_.isEqual}
                               subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
                        {(fprops) => (
                            <Form onSubmit={fprops.handleSubmit}>
                                <Field name="name" component={ReduxFormField} as="input"
                                       format={formatters.trim} formatOnBlur
                                       label={Translate.string('Name')}
                                       disabled={fprops.submitting}
                                       autoFocus />
                                <Field name="features" component={ReduxDropdownField}
                                       multiple selection options={featureOptions}
                                       label={Translate.string('Features')}
                                       disabled={fprops.submitting} />
                                <Form.Button type="submit"
                                             disabled={(
                                                 fprops.hasValidationErrors ||
                                                 fprops.pristine ||
                                                 fprops.submitting
                                             )}
                                             loading={fprops.submitting} primary
                                             content={Translate.string('Add')} />
                            </Form>
                        )}
                    </FinalForm>
                </Modal.Content>
            </Modal>
        );
    }
}


class EquipmentTypesPage extends React.PureComponent {
    static propTypes = {
        isFetching: PropTypes.bool.isRequired,
        features: PropTypes.array.isRequired,
        equipmentTypes: PropTypes.array.isRequired,
        actions: PropTypes.exact({
            fetchEquipmentTypes: PropTypes.func.isRequired,
            deleteEquipmentType: PropTypes.func.isRequired,
            updateEquipmentType: PropTypes.func.isRequired,
            createEquipmentType: PropTypes.func.isRequired,
            fetchFeatures: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {
        adding: false,
    };

    componentDidMount() {
        const {actions: {fetchEquipmentTypes, fetchFeatures}} = this.props;
        fetchEquipmentTypes();
        fetchFeatures();
    }

    handleAddClick = () => {
        this.setState({adding: true});
    };

    handleAddClose = () => {
        this.setState({adding: false});
    };

    handleCreate = async (data) => {
        const {actions: {createEquipmentType}} = this.props;
        const rv = await createEquipmentType(data);
        if (!rv.error) {
            this.setState({adding: false});
        }
        return rv;
    };

    render() {
        const {
            isFetching, equipmentTypes, features,
            actions: {deleteEquipmentType, updateEquipmentType},
        } = this.props;
        const {adding} = this.state;

        return (
            <>
                <Header as="h2" styleName="page-header">
                    <Translate>
                        Equipment types
                    </Translate>
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
                            {equipmentTypes.map(eq => (
                                <EquipmentType key={eq.id}
                                               {...eq}
                                               availableFeatures={features}
                                               deleteEquipmentType={deleteEquipmentType}
                                               updateEquipmentType={updateEquipmentType} />
                            ))}
                        </List>
                        {adding && (
                            <AddEquipmentTypeModal onSubmit={this.handleCreate}
                                                   onClose={this.handleAddClose}
                                                   features={features} />
                        )}
                    </>
                )}
            </>
        );
    }
}

export default connect(
    state => ({
        isFetching: adminSelectors.isFetchingFeaturesOrEquipmentTypes(state),
        equipmentTypes: adminSelectors.getEquipmentTypes(state),
        features: adminSelectors.getFeatures(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchEquipmentTypes: adminActions.fetchEquipmentTypes,
            deleteEquipmentType: adminActions.deleteEquipmentType,
            updateEquipmentType: adminActions.updateEquipmentType,
            createEquipmentType: adminActions.createEquipmentType,
            fetchFeatures: adminActions.fetchFeatures,
        }, dispatch),
    })
)(EquipmentTypesPage);
