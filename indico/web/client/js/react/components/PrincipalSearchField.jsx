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

/* eslint "react/no-unused-state": "off" */

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Dropdown, Label} from 'semantic-ui-react';

import searchUsersURL from 'indico-url:users.user_search';
import searchGroupsURL from 'indico-url:groups.group_search';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';


const searchUser = async (data) => {
    let response;
    try {
        response = await indicoAxios.get(searchUsersURL(data));
    } catch (error) {
        handleAxiosError(error);
        return;
    }
    return response.data.data;
};

const searchGroups = async (data) => {
    let response;
    try {
        response = await indicoAxios.get(searchGroupsURL(data));
    } catch (error) {
        handleAxiosError(error);
        return;
    }

    return response.data;
};

export default class PrincipalSearchField extends React.Component {
    static propTypes = {
        multiple: PropTypes.bool,
        value: PropTypes.oneOfType([
            PropTypes.object,
            PropTypes.array
        ]),
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        withGroups: PropTypes.bool
    };

    static defaultProps = {
        multiple: false,
        value: null,
        disabled: false,
        withGroups: false
    };

    constructor(props) {
        super(props);

        const {multiple, onChange} = this.props;
        let {value} = this.props;
        let dropdownValue;

        if (multiple) {
            value = value || [];
            dropdownValue = value.map((val) => val.identifier);
        } else {
            dropdownValue = value && value.identifier;
        }

        this.state = {
            isFetching: false,
            options: [],
            prevPropsValue: dropdownValue,
            value: dropdownValue
        };

        if (multiple) {
            this.userCache = Object.assign({}, ...value.map((val) => ({[val.identifier]: val})));
        } else {
            this.userCache = {};
        }

        onChange(value);
    }

    static getDerivedStateFromProps({value, multiple}, state) {
        let valuesChanged, newValue;
        if (multiple) {
            newValue = value.map((val) => val.identifier);
            valuesChanged = !_.isEqual(newValue.sort(), state.prevPropsValue.sort());
        } else {
            valuesChanged = value !== state.prevPropsValue;
            newValue = value;
        }

        if (valuesChanged) {
            return {
                ...state,
                prevPropsValue: newValue,
                value: newValue
            };
        }
        return null;
    }

    renderItem = ({is_group: isGroup, ...itemData}) => (isGroup ? {
        text: itemData.name,
        value: itemData.identifier,
        key: itemData.identifier,
        icon: 'users'
    } : {
        text: itemData.full_name,
        description: itemData.email,
        value: itemData.identifier,
        key: itemData.identifier,
        icon: 'user'
    });

    handleSearchChange = _.debounce(async (__, {searchQuery}) => {
        if (searchQuery.trim().length < 3) {
            return;
        }

        this.setState({
            isFetching: true
        });

        const query = (searchQuery.indexOf('@') !== -1) ? {email: searchQuery} : {name: searchQuery};
        const {withGroups} = this.props;
        const promises = [];

        promises.push(searchUser(query));
        if (withGroups) {
            promises.push(searchGroups({name: searchQuery}));
        }

        const principals = await Promise.all(promises);
        const items = [];
        for (const principalList of principals) {
            items.push(...principalList);
        }

        this.userCache = Object.assign(this.userCache, ...items.map(item => ({[item.identifier]: item})));
        this.setState({
            isFetching: false,
            options: items.map(this.renderItem)
        });
    }, 500);

    render() {
        const {multiple, onChange, disabled} = this.props;
        const {isFetching, options, value} = this.state;
        let dropdownValues, selectedValues, dropdownOptions;
        let placeholder = Translate.string('Write a name (of the group or user) or e-mail...');

        if (multiple) {
            dropdownValues = value || [];
            selectedValues = dropdownValues.map((id) => this.userCache[id]).map(this.renderItem);
            dropdownOptions = isFetching ? selectedValues : options.concat(selectedValues);

            if (!dropdownValues.length && disabled) {
                placeholder = Translate.string('Nobody');
            }
        } else {
            dropdownValues = value ? value : null;
            dropdownOptions = options;
        }

        const renderDisabledLabel = (item) => (
            <Label key={item.key} icon={item.icon} content={item.text} removeIcon={null} />
        );
        const dropdownProps = disabled ? {icon: null, renderLabel: renderDisabledLabel} : {search: opts => opts};
        return (
            <Dropdown deburr
                      selection
                      fluid
                      {...dropdownProps}
                      minCharacters={3}
                      multiple={multiple}
                      options={dropdownOptions}
                      value={dropdownValues}
                      placeholder={placeholder}
                      onChange={(__, {value: val}) => {
                          let fieldValue;
                          if (multiple) {
                              fieldValue = val.map((id) => this.userCache[id]);
                          } else {
                              fieldValue = this.userCache[val];
                          }

                          this.setState({value: val});
                          onChange(fieldValue);
                      }}
                      onSearchChange={this.handleSearchChange}
                      disabled={isFetching || disabled}
                      loading={isFetching}
                      noResultsMessage={isFetching ? null : Translate.string('No results found')} />
        );
    }
}
