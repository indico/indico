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
import {Form, Icon} from 'semantic-ui-react';

import {FilterFormComponent} from '../../../common/filters';


export default class EquipmentForm extends FilterFormComponent {
    static propTypes = {
        selectedEquipment: PropTypes.arrayOf(PropTypes.string).isRequired,
        selectedFeatures: PropTypes.arrayOf(PropTypes.string).isRequired,
        availableEquipment: PropTypes.arrayOf(PropTypes.string).isRequired,
        availableFeatures: PropTypes.arrayOf(PropTypes.shape({
            name: PropTypes.string.isRequired,
            title: PropTypes.string.isRequired,
        })).isRequired,
        ...FilterFormComponent.propTypes
    };

    constructor(props) {
        super(props);
        const {availableEquipment, availableFeatures, selectedEquipment, selectedFeatures} = props;
        this.state = {
            equipment: availableEquipment.filter(eq => selectedEquipment.includes(eq)),
            features: availableFeatures.map(f => f.name).filter(f => selectedFeatures.includes(f)),
        };
    }

    setEquipment(eqName, value) {
        const {setParentField} = this.props;

        this.setState((oldState) => {
            const equipmentList = _.without(oldState.equipment, eqName);
            if (value) {
                equipmentList.push(eqName);
            }
            return {
                equipment: equipmentList
            };
        }, () => {
            setParentField('equipment', this.state.equipment);
        });
    }

    setFeature(featName, value) {
        const {setParentField} = this.props;

        this.setState((oldState) => {
            const featureList = _.without(oldState.features, featName);
            if (value) {
                featureList.push(featName);
            }
            return {features: featureList};
        }, () => {
            setParentField('features', this.state.features);
        });
    }

    render() {
        const {availableEquipment, availableFeatures} = this.props;
        const {equipment, features} = this.state;
        return (
            <>
                <Form.Group>
                    {availableFeatures.map(feat => (
                        <Form.Checkbox checked={features.includes(feat.name)}
                                       key={feat.name}
                                       label={
                                           <label>
                                               <Icon name={feat.icon} />
                                               <strong>{feat.title}</strong>
                                           </label>
                                       }
                                       onChange={(__, {checked}) => {
                                           this.setFeature(feat.name, checked);
                                       }} />
                    ))}
                    {!!availableFeatures.length && !!availableEquipment.length && <br />}
                    {availableEquipment.map(equip => (
                        <Form.Checkbox checked={equipment.includes(equip)}
                                       key={equip}
                                       label={equip}
                                       onChange={(__, {checked}) => {
                                           this.setEquipment(equip, checked);
                                       }} />
                    ))}
                </Form.Group>
            </>
        );
    }
}
