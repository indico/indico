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
import {connect} from 'react-redux';
import _ from 'lodash';
import {Dropdown, Icon, List} from 'semantic-ui-react';
import * as roomsSelectors from './selectors';

import './EquipmentList.module.scss';


class EquipmentList extends React.Component {
    static propTypes = {
        onChange: PropTypes.func.isRequired,
        onFocus: PropTypes.func.isRequired,
        onBlur: PropTypes.func.isRequired,
        value: PropTypes.array.isRequired,
        label: PropTypes.string.isRequired,
        equipmentTypes: PropTypes.arrayOf(PropTypes.object).isRequired,
    };

    generateEquipmentOptions = () => {
        const {value} = this.props;
        const {equipmentTypes} = this.props;
        return equipmentTypes
            .filter(eq => !value.includes(eq.id))
            .map(eq => ({key: eq.id, text: eq.name, value: eq.id}));
    };

    render() {
        const {onChange, onFocus, onBlur, value, equipmentTypes, label} = this.props;
        if (!equipmentTypes || !value) {
            return;
        }
        const equipmentTypesMapped = _.mapKeys(equipmentTypes, 'id');
        const options = this.generateEquipmentOptions();
        return (
            <>
                <Dropdown button
                          text={label}
                          className="icon"
                          floating
                          labeled
                          icon="add"
                          options={options}
                          search
                          onFocus={onFocus}
                          onBlur={onBlur}
                          disabled={options.length === 0}
                          selectOnBlur={false}
                          onChange={(event, values) => {
                              onChange([...value, values.value]);
                          }} />
                <List key="equipment" divided>
                    {value.map((equipmentId) => (
                        <List.Item key={equipmentTypesMapped[equipmentId].id}>
                            <List.Content floated="right">
                                <Icon styleName="equipment-button" name="trash" onClick={() => {
                                    _.remove(value, (n) => {
                                        return n === equipmentId;
                                    });
                                    onChange([...value]);
                                }} />
                            </List.Content>
                            <List.Content>{equipmentTypesMapped[equipmentId].name}</List.Content>
                        </List.Item>
                    ))}
                </List>
            </>
        );
    }
}

export default connect(
    (state) => ({
        equipmentTypes: roomsSelectors.getEquipmentTypes(state)
    })
)(EquipmentList);
