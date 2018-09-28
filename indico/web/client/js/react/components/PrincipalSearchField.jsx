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
import {Dropdown, Icon, Label} from 'semantic-ui-react';

import searchUsersURL from 'indico-url:users.user_search';
import searchGroupsURL from 'indico-url:groups.group_search';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';
import camelizeKeys from 'indico/utils/camelize';


const searchUser = async (data) => {
    let response;
    try {
        response = await indicoAxios.get(searchUsersURL(), {params: {...data, favorites_first: true}});
    } catch (error) {
        handleAxiosError(error);
        return;
    }
    return camelizeKeys(response.data.data);
};

const searchGroups = async (data) => {
    let response;
    try {
        response = await indicoAxios.get(searchGroupsURL(data));
    } catch (error) {
        handleAxiosError(error);
        return;
    }

    return camelizeKeys(response.data);
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
        withGroups: PropTypes.bool,
        favoriteUsers: PropTypes.array
    };

    static defaultProps = {
        multiple: false,
        value: null,
        disabled: false,
        withGroups: false,
        favoriteUsers: []
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
            value: dropdownValue,
            searchQuery: ''
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

    isInFavorites = (userId) => {
        const {favoriteUsers} = this.props;
        return favoriteUsers.some((favoriteUser) => favoriteUser.id === userId);
    };

    renderItem = ({isGroup, ...itemData}) => (isGroup ? {
        text: itemData.name,
        value: itemData.identifier,
        key: itemData.identifier,
        icon: 'users'
    } : {
        text: itemData.fullName,
        description: itemData.email,
        value: itemData.identifier,
        key: itemData.identifier,
        icon: <Icon color={this.isInFavorites(itemData.id) ? 'yellow' : null} name={this.isInFavorites(itemData.id) ? 'star' : 'user'} />
    });

    sortPrincipals = (a, b) => {
        const {withGroups} = this.props;
        if (withGroups) {
            if (a.isGroup && b.isGroup) {
                return a.name.localeCompare(b.name);
            } else if (a.isGroup) {
                return 1;
            } else if (b.isGroup) {
                return -1;
            }
        }

        const isAInFavorites = this.isInFavorites(a.id);
        const isBInFavorites = this.isInFavorites(b.id);
        if (isAInFavorites && isBInFavorites) {
            return a.fullName.localeCompare(b.fullName);
        } else if (isAInFavorites) {
            return -1;
        } else if (isBInFavorites) {
            return 1;
        } else {
            return a.fullName.localeCompare(b.fullName);
        }
    };

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
            options: items.sort(this.sortPrincipals).map(this.renderItem)
        });
    }, 1000);

    render() {
        const {multiple, onChange, disabled, withGroups} = this.props;
        const {isFetching, options, value, searchQuery} = this.state;
        let dropdownValues, selectedValues, dropdownOptions, placeholder;

        if (withGroups) {
            placeholder = Translate.string('Write a name (of the group or user) or e-mail...');
        } else {
            placeholder = Translate.string('Write a name of the user or e-mail...');
        }

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
        const searchInput = {
            onChange: ({target: {value: inputValue}}) => this.setState({searchQuery: inputValue}),
            disabled: isFetching || disabled
        };
        return (
            <Dropdown deburr
                      selection
                      fluid
                      closeOnChange
                      {...dropdownProps}
                      minCharacters={3}
                      searchInput={searchInput}
                      searchQuery={searchQuery}
                      multiple={multiple}
                      options={dropdownOptions}
                      value={dropdownValues}
                      placeholder={placeholder}
                      onOpen={() => this.setState({options: []})}
                      onChange={(__, {value: val}) => {
                          let fieldValue;
                          if (multiple) {
                              fieldValue = val.map((id) => this.userCache[id]);
                          } else {
                              fieldValue = this.userCache[val];
                          }

                          this.setState({value: val, searchQuery: ''});
                          onChange(fieldValue);
                      }}
                      onSearchChange={this.handleSearchChange}
                      disabled={isFetching || disabled}
                      loading={isFetching}
                      noResultsMessage={isFetching ? null : Translate.string('No results found')} />
        );
    }
}
