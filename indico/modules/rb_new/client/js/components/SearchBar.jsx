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

import isEqual from 'lodash/isEqual';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Form, Icon, Input, Popup, Select} from 'semantic-ui-react';
import {DebounceInput} from 'react-debounce-input';

import {Translate} from 'indico/react/i18n';
import {parseSearchBarText} from '../util';

import './SearchBar.module.scss';


export default class SearchBar extends React.Component {
    static propTypes = {
        setTextFilter: PropTypes.func.isRequired,
        setAdvancedFilter: PropTypes.func.isRequired,
        fetchBuildings: PropTypes.func.isRequired,
        onConfirm: PropTypes.func.isRequired,
        filters: PropTypes.object.isRequired,
        buildings: PropTypes.object.isRequired
    };

    constructor(props) {
        super(props);
        this.state = {
            filtersVisible: false,
            filtersChanged: false,
            text: '',
            building: '',
            floor: ''
        };
    }

    componentDidMount() {
        const {fetchBuildings} = this.props;
        fetchBuildings();
    }

    componentWillUnmount() {
        const {setAdvancedFilter} = this.props;
        setAdvancedFilter('text', '');
    }

    toggleFiltersPopup(visible) {
        this.setState({filtersVisible: visible});
    }

    onClose() {
        const {filtersChanged} = this.state;
        this.toggleFiltersPopup(false);
        if (filtersChanged) {
            this.applyFilters();
            this.setState({filtersChanged: false});
        }
    }

    applyFilters() {
        const {onConfirm} = this.props;
        onConfirm();
    }

    updateTextFilter(filterValue) {
        const {setTextFilter, filters: {text}} = this.props;

        if (filterValue === text) {
            return;
        }

        const parsedValues = parseSearchBarText(filterValue);
        if (isEqual(parsedValues, parseSearchBarText(text))) {
            return;
        }

        const stateUpdates = {text: filterValue, filtersChanged: false};
        stateUpdates.building = parsedValues.building;
        stateUpdates.floor = parsedValues.floor;

        this.updateComponentState('text', stateUpdates);
        setTextFilter(filterValue);
    }

    updateFilter(filterName, value) {
        const stateUpdates = {[filterName]: value};

        if (filterName === 'building') {
            stateUpdates.floor = '';
        }

        // eslint-disable-next-line react/destructuring-assignment
        if (this.state[filterName] !== value) {
            stateUpdates.filtersChanged = true;
        }

        this.updateComponentState(filterName, stateUpdates);
    }

    updateComponentState(filterName, newState) {
        this.setState(newState, () => {
            let textValue = '';
            const {setAdvancedFilter} = this.props;
            const {text: stateText} = this.state;

            if (filterName === 'text') {
                textValue = stateText;
            } else {
                const stateToKeys = {building: 'bldg', floor: 'floor'};
                let textParts = Object.entries(stateToKeys).filter(([stateKey]) => {
                    return !!this.state[stateKey]; // eslint-disable-line react/destructuring-assignment
                }).map(([stateKey, searchKey]) => {
                    return `${searchKey}:${this.state[stateKey]}`; // eslint-disable-line react/destructuring-assignment
                });

                const text = parseSearchBarText(stateText).text;
                if (text) {
                    textParts = [text, ...textParts];
                }

                textValue = textParts.join(' ');
            }

            this.setState({text: textValue});
            setAdvancedFilter('text', textValue);
        });
    }

    render() {
        const commonAttrs = {
            search: true,
            selection: true
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
            value: key
        }));
        const content = (
            <Form>
                <Form.Field>
                    <Select {...commonAttrs} placeholder={Translate.string('Select building')}
                            loading={isFetching}
                            onChange={(event, data) => this.updateFilter('building', data.value)}
                            value={building}
                            options={[{text: '', value: ''}, ...buildings]} />
                </Form.Field>
                <Form.Field>
                    <Select {...commonAttrs} placeholder={Translate.string('Select floor')} disabled={!building}
                            onChange={(event, data) => this.updateFilter('floor', data.value)}
                            value={floor}
                            options={[{text: '', value: ''}, ...floors]} />
                </Form.Field>
                <Form.Field>
                    <Button primary onClick={() => this.onClose()} disabled={!filtersChanged}>
                        <Translate>Apply</Translate>
                    </Button>
                </Form.Field>
            </Form>
        );

        const {filtersVisible, text} = this.state;
        let inputIcon;
        if (text) {
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
                       onClose={() => this.onClose()}
                       open={filtersVisible}
                       content={content}
                       position="bottom left"
                       on="click" />
                <DebounceInput element={Input}
                               styleName="text-filter"
                               icon={inputIcon}
                               debounceTimeout={300}
                               onChange={(event) => this.updateTextFilter(event.target.value)}
                               value={text} />
            </div>
        );
    }
}
