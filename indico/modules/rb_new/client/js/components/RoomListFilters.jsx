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
import {Button, Form, Icon, Input, Popover, Select} from 'antd';
import propTypes from 'prop-types';
import {DebounceInput} from 'react-debounce-input';

import {Translate} from 'indico/react/i18n';
import {parseRoomListFiltersText} from '../util';

import './RoomListFilters.module.scss';


export default class RoomListFilters extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            filtersVisible: false,
            text: null,
            building: null,
            floor: null
        };
    }

    componentDidMount() {
        const {fetchBuildings} = this.props;
        fetchBuildings();
    }

    handleVisibleChange(visible) {
        this.setState({filtersVisible: visible});
    }

    applyFilters() {
        const {onConfirm} = this.props;
        this.setState({filtersVisible: false});
        onConfirm();
    }

    handleFiltersChange(filter, value) {
        const {setTextParamFilter, setAdvancedParamFilter, filters: {text}} = this.props;
        const stateUpdates = {[filter]: value};

        if (filter === 'building') {
            stateUpdates.floor = null;
        } else if (filter === 'text') {
            const parsedValues = parseRoomListFiltersText(value);

            stateUpdates.building = parsedValues.building;
            stateUpdates.floor = parsedValues.floor;
        }

        this.setState(stateUpdates, () => {
            let textValue = null;
            const {building, floor} = this.state;

            if (filter === 'text') {
                textValue = value;
            } else {
                if (building) {
                    textValue = `building:${building}`;
                }

                if (floor) {
                    textValue += ` floor:${floor}`;
                }
            }

            this.setState({text: textValue});
            setAdvancedParamFilter('text', textValue);
        });

        if (filter === 'text') {
            if (value.trim() !== text.trim()) {
                setTextParamFilter(value);
            }
        }
    }

    render() {
        const commonAttrs = {
            showSearch: true,
            allowClear: true,
            style: {width: 200},
            getPopupContainer: (target) => target.parentNode,
            filterOption: (input, option) => option.props.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
        };

        const {buildings: {list: buildingsList}} = this.props;
        const {building, floor} = this.state;
        const content = (
            <Form>
                <Form.Item>
                    <Select {...commonAttrs} placeholder="Select building"
                            onChange={(value) => this.handleFiltersChange('building', value)}
                            value={building}>
                        {Object.keys(buildingsList).map(buildingItem => (
                            <Select.Option key={buildingItem}>
                                {buildingsList[buildingItem].title}
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>
                <Form.Item>
                    <Select {...commonAttrs} placeholder="Select floor" disabled={!building}
                            onChange={(value) => this.handleFiltersChange('floor', value)}
                            value={floor}>
                        {building && buildingsList[building] &&
                            buildingsList[building].floors.map((floorItem) => (
                                <Select.Option key={floorItem}>{floorItem}</Select.Option>
                            ))
                        }
                    </Select>
                </Form.Item>
                <Form.Item>
                    <Button type="primary" onClick={this.applyFilters.bind(this)}>
                        <Translate>Apply filters</Translate>
                    </Button>
                </Form.Item>
            </Form>
        );

        const {filtersVisible, text} = this.state;
        const selectBefore = (
            <Popover content={content}
                     placement="bottomLeft"
                     trigger="click"
                     visible={filtersVisible}
                     onVisibleChange={this.handleVisibleChange.bind(this)}>
                <span styleName="filters-trigger">
                    <Translate>
                        Filters
                    </Translate>
                    <Icon styleName="filters-down-arrow" type="down" />
                </span>
            </Popover>
        );

        return (
            <div styleName="text-filter">
                <DebounceInput element={Input}
                               debounceTimeout={300}
                               addonBefore={selectBefore}
                               onChange={(event) => this.handleFiltersChange('text', event.target.value)}
                               value={text} />
            </div>
        );
    }
}

RoomListFilters.propTypes = {
    setTextParamFilter: propTypes.func.isRequired,
    setAdvancedParamFilter: propTypes.func.isRequired,
    fetchBuildings: propTypes.func.isRequired,
    onConfirm: propTypes.func.isRequired,
    filters: propTypes.object.isRequired,
    buildings: propTypes.object.isRequired
};
