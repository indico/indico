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

import PropTypes from 'prop-types';
import React from 'react';
import {Button, Form, Icon, Input, Popup, Select} from 'semantic-ui-react';
import {DebounceInput} from 'react-debounce-input';

import {Translate} from 'indico/react/i18n';
import {parseSearchBarText} from '../util';

import './SearchBar.module.scss';


export default class SearchBar extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        fetchBuildings: PropTypes.func.isRequired,
        filters: PropTypes.object.isRequired,
        buildings: PropTypes.object.isRequired,
        onConfirm: PropTypes.func.isRequired,
        onTextChange: PropTypes.func.isRequired
    };

    constructor(props) {
        super(props);

        const {filters: {building, floor, text}} = this.props;
        this.state = {
            filtersPopupVisible: false,
            filtersChanged: false,
            inputTextValue: null,
            roomName: text,
            building,
            floor
        };
    }

    componentDidMount = () => {
        this.props.fetchBuildings(); // eslint-disable-line react/destructuring-assignment
        this.setState({inputTextValue: this.composeInputTextValue()});
    }

    componentWillUnmount = () => {
        this.props.setFilterParameter('text', null); // eslint-disable-line react/destructuring-assignment
        this.setState({building: null, floor: null, roomName: null, inputTextValue: null});
    }

    toggleFiltersPopup = (visible) => {
        this.setState({filtersPopupVisible: visible});
    }

    close = () => {
        const {filtersChanged} = this.state;
        this.toggleFiltersPopup(false);

        if (filtersChanged) {
            const {onConfirm} = this.props;
            onConfirm();
            this.setState({filtersChanged: false});
        }
    }

    composeInputTextValue = () => {
        const stateToKeys = {building: 'bldg', floor: 'floor'};
        const {roomName} = this.state;

        let textParts = Object.entries(stateToKeys)
            .filter(([stateKey]) => {
                return !!this.state[stateKey]; // eslint-disable-line react/destructuring-assignment
            })
            .map(([stateKey, searchKey]) => {
                return `${searchKey}:${this.state[stateKey]}`; // eslint-disable-line react/destructuring-assignment
            });

        if (roomName) {
            textParts = [roomName, ...textParts];
        }

        return textParts.length ? textParts.join(' ') : null;
    }

    didFiltersChange = () => {
        const {filters} = this.props;
        const {building, floor, roomName} = this.state;

        return roomName !== filters.text || building !== filters.building || floor !== filters.floor;
    }

    updateTextFilter = (filterValue) => {
        const {setFilterParameter, onTextChange} = this.props;
        const {building, text: roomName, floor} = parseSearchBarText(filterValue);
        const stateUpdates = {inputTextValue: filterValue, building, floor, roomName};

        this.setState(stateUpdates, () => {
            this.composeInputTextValue();
            setFilterParameter('text', filterValue);
            onTextChange();
        });
    }

    updateFilter = (filterName, value) => {
        const filterValue = value || null;
        const stateChanges = {[filterName]: filterValue};
        const {setFilterParameter} = this.props;

        if (filterName === 'building') {
            stateChanges.floor = null;
        }

        this.setState(stateChanges, () => {
            const inputTextValue = this.composeInputTextValue();
            this.setState({inputTextValue, filtersChanged: this.didFiltersChange()});
            setFilterParameter('text', inputTextValue);
        });
    }

    render() {
        const commonAttrs = {
            search: true
        };

        const {buildings: {list: buildingsList, isFetching}} = this.props;
        const {building, floor, filtersChanged} = this.state;
        let floors = [];

        if (building && buildingsList[building]) {
            floors = buildingsList[building].floors.map((floorItem) => ({
                text: floorItem, value: floorItem
            }));
        }

        const buildings = Object.entries(buildingsList).map(([key, val]) => ({
            text: Translate.string('Building {number}', {number: val.number}),
            value: parseInt(key, 10)
        }));

        const content = (
            <Form>
                <Form.Field>
                    <Select {...commonAttrs} placeholder={Translate.string('Select building')}
                            loading={isFetching}
                            onChange={(event, data) => this.updateFilter('building', data.value)}
                            value={building && parseInt(building, 10)}
                            options={[{text: '', value: ''}, ...buildings]} />
                </Form.Field>
                <Form.Field>
                    <Select {...commonAttrs} placeholder={Translate.string('Select floor')} disabled={!building}
                            onChange={(event, data) => this.updateFilter('floor', data.value)}
                            value={floor}
                            options={[{text: '', value: ''}, ...floors]} />
                </Form.Field>
                <Form.Field>
                    <Button primary onClick={this.close} disabled={!filtersChanged}>
                        <Translate>Apply</Translate>
                    </Button>
                </Form.Field>
            </Form>
        );

        const {filtersPopupVisible, inputTextValue} = this.state;
        let inputIcon;
        if (inputTextValue) {
            inputIcon = <Icon link name="remove" onClick={() => this.updateTextFilter('')} />;
        } else {
            inputIcon = <Icon name="search" />;
        }

        const popupTrigger = (
            <Button attached="left" icon onClick={() => this.toggleFiltersPopup(true)}>
                <Translate>Advanced</Translate>
                <Icon name="caret down" />
            </Button>
        );

        return (
            <div styleName="room-filters">
                <Popup trigger={popupTrigger}
                       onClose={this.close}
                       open={filtersPopupVisible}
                       content={content}
                       position="bottom left"
                       on="click" />
                <DebounceInput element={Input}
                               styleName="text-filter"
                               icon={inputIcon}
                               debounceTimeout={300}
                               onChange={(event) => this.updateTextFilter(event.target.value)}
                               value={inputTextValue || ''} />
            </div>
        );
    }
}
