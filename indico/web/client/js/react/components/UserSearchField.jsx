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

export default class UserSearchField extends React.Component {
    static propTypes = {
        multiple: PropTypes.bool,
        defaultValue: PropTypes.object,
        onChange: PropTypes.func.isRequired,
        disabled: PropTypes.bool
    };

    static defaultProps = {
        multiple: false,
        defaultValue: null,
        disabled: false
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

    static getDerivedStateFromProps({value: {id: userId}}, state) {
        if (userId !== state.prevPropsUserId) {
            return {
                ...state,
                prevPropsUserId: userId,
                userId
            };
        }
        return null;
    }

    renderUser({first_name: firstName, last_name: lastName, email, id}) {
        return {
            text: `${firstName} ${lastName}`,
            description: email,
            value: id,
            key: id
        };
    }

    handleSearchChange = _.debounce(async (__, {searchQuery}) => {
        if (searchQuery.trim().length < 3) {
            return;
        }

        this.setState({
            isFetching: true
        });
        const query = (searchQuery.indexOf('@') !== -1)
            ? {email: searchQuery}
            : {name: searchQuery};
        const users = await searchUser(query);
        const options = users.map(this.renderUser);
        this.userCache = Object.assign(this.userCache, ...users.map(user => ({[user.id]: user})));
        this.setState({
            isFetching: false,
            options
        });
    }, 500);

    render() {
        const {multiple, onChange, disabled} = this.props;
        const {isFetching, options, userId} = this.state;

        return (
            <Dropdown search={opts => opts}
                      deburr
                      selection
                      fluid
                      minCharacters={3}
                      multiple={multiple}
                      options={options}
                      value={userId}
                      placeholder={Translate.string('Write a name or e-mail...')}
                      onChange={(__, {value: id}) => {
                          const val = this.userCache[id];
                          this.setState({
                              userId: id
                          });
                          onChange(val);
                      }}
                      onSearchChange={this.handleSearchChange}
                      disabled={isFetching || disabled}
                      loading={isFetching} />
        );
    }
}
