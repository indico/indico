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

import {Translate} from 'indico/react/i18n';

import FilterFormComponent from './FilterFormComponent';


export default class EquipmentForm extends FilterFormComponent {
    static propTypes = {
        possibleEquipment: PropTypes.arrayOf(PropTypes.string).isRequired,
        selectedEquipment: PropTypes.arrayOf(PropTypes.string),
        ...FilterFormComponent.propTypes
    };

    constructor(props) {
        super(props);
        const {possibleEquipment, selectedEquipment} = props;
        this.state = {
            equipment: possibleEquipment.filter(eq => selectedEquipment.indexOf(eq) >= 0)
        };
    }

    static getDerivedStateFromProps({selectedEquipment}, prevState) {
        return {equipment: selectedEquipment, ...prevState};
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

    resetSelection = () => {
        const {possibleEquipment} = this.props;
        possibleEquipment.forEach(eq => {
            this.setEquipment(eq, false);
        });
    };

    render() {
        const {possibleEquipment} = this.props;
        const {equipment} = this.state;
        return (
            <>
                <Form.Group>
                    {possibleEquipment.map(equip => (
                        <Form.Checkbox checked={equipment.indexOf(equip) >= 0}
                                       key={equip}
                                       label={equip}
                                       onChange={(_, {checked}) => {
                                           this.setEquipment(equip, checked);
                                       }} />
                    ))}
                </Form.Group>
                {!!equipment.length && (
                    <div style={{marginTop: '1em'}}>
                        <Form.Button fluid basic color="red" size="mini" onClick={this.resetSelection}>
                            <Icon name="remove" circular />
                            <Translate>Reset</Translate>
                        </Form.Button>
                    </div>
                )}
            </>
        );
    }
}
