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
import {Dropdown} from 'semantic-ui-react';

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
        defaultValue: PropTypes.object,
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool,
        withGroups: PropTypes.bool
    };

    static defaultProps = {
        multiple: false,
        defaultValue: null,
        disabled: false,
        withGroups: false
    };

    constructor(props) {
        super(props);
        const {defaultValue} = this.props;
        const userId = defaultValue && defaultValue.id;

        this.state = {
            isFetching: false,
            options: [],
            prevPropsUserId: userId,
            userId
        };
        this.userCache = {};
    }

    static getDerivedStateFromProps({value: {id: userId}, multiple}, state) {
        const valuesChanged = multiple ? !_.isEqual(userId, state.prevPropsUserId) : userId !== state.prevPropsUserId;
        if (valuesChanged) {
            return {
                ...state,
                prevPropsUserId: userId,
                userId
            };
        }
        return null;
    }

    renderItem = ({is_group: isGroup, ...itemData}) => (isGroup ? {
        text: itemData.name,
        value: itemData.name,
        key: itemData.name,
        icon: 'users'
    } : {
        text: `${itemData.first_name} ${itemData.last_name}`,
        description: itemData.email,
        value: itemData.id,
        key: itemData.id,
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

        this.userCache = Object.assign(this.userCache, ...items.map(item => ({[item.id]: item})));
        this.setState({
            isFetching: false,
            options: items.map(this.renderItem)
        });
    }, 500);

    render() {
        const {multiple, onChange, disabled} = this.props;
        const {isFetching, options, userId} = this.state;
        let dropdownValues, selectedValues, dropdownOptions;

        if (multiple) {
            dropdownValues = userId === undefined ? [] : userId;
            selectedValues = dropdownValues.map((id) => this.userCache[id]).map(this.renderItem);
            dropdownOptions = isFetching ? selectedValues : options.concat(selectedValues);
        } else {
            dropdownValues = selectedValues = userId;
            dropdownOptions = options;
        }

        return (
            <Dropdown search={opts => opts}
                      deburr
                      selection
                      fluid
                      minCharacters={3}
                      multiple={multiple}
                      options={dropdownOptions}
                      value={dropdownValues}
                      placeholder={Translate.string('Write a name (of the group or user) or e-mail...')}
                      onChange={(__, {value}) => {
                          let fieldValue;
                          if (multiple) {
                              fieldValue = value.map((id) => this.userCache[id]);
                          } else {
                              fieldValue = this.userCache[value];
                          }

                          this.setState({
                              userId: value
                          });
                          onChange(fieldValue);
                      }}
                      onSearchChange={this.handleSearchChange}
                      disabled={isFetching || disabled}
                      loading={isFetching}
                      noResultsMessage={isFetching ? null : Translate.string('No results found')} />
        );
    }
}
