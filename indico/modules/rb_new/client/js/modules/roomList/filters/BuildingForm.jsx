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
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import {FilterFormComponent} from '../../../common/filters';


export default class BuildingForm extends FilterFormComponent {
    static propTypes = {
        buildings: PropTypes.array.isRequired,
        building: PropTypes.string,
        ...FilterFormComponent.propTypes
    };

    static defaultProps = {
        building: null
    };

    constructor(props) {
        super(props);

        const {building} = this.props;
        this.state = {building};
    }

    setBuilding = (building) => {
        const {setParentField} = this.props;

        this.setState({building}, () => {
            setParentField('building', building);
        });
    };

    render() {
        const {buildings} = this.props;
        const {building} = this.state;
        const options = buildings.map((buildingNumber) => ({
            text: Translate.string('Building {buildingNumber}', {buildingNumber}),
            value: buildingNumber
        }));

        return (
            <>
                <Form.Group>
                    <Form.Dropdown options={options}
                                   value={building}
                                   onChange={(__, {value}) => this.setBuilding(value || null)}
                                   closeOnChange
                                   closeOnBlur
                                   search
                                   selection
                                   clearable />
                </Form.Group>
            </>
        );
    }
}
