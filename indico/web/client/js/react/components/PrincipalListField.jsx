/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

import principalsURL from 'indico-url:core.principals';

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Icon, List, Loader} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {useAsyncEffect} from '../hooks';

import './PrincipalListField.module.scss';


/**
 * A field that lets the user select a list of users/groups
 */
const PrincipalListField = (props) => {
    const {value, disabled, onChange, onFocus, onBlur} = props;

    const isGroup = identifier => identifier.startsWith('Group:');
    const handleDelete = identifier => {
        onChange(value.filter(x => x !== identifier));
        onFocus();
        onBlur();
    };

    // keep track of details for each entry
    const [identifierMap, setIdentifierMap] = useState({});

    // fetch missing details
    useAsyncEffect(async () => {
        const missingData = _.difference(value, Object.keys(identifierMap));
        if (!missingData.length) {
            return;
        }

        let response;
        try {
            response = await indicoAxios.post(principalsURL(), {values: missingData});
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        setIdentifierMap(prev => ({...prev, ...response.data}));
    }, [identifierMap, value]);

    const entries = _.sortBy(
        value.filter(x => x in identifierMap).map(x => identifierMap[x]),
        x => `${x.group ? 0 : 1}-${x.name.toLowerCase()}`
    );
    const pendingEntries = _.sortBy(
        value.filter(x => !(x in identifierMap)).map(x => ({identifier: x, group: isGroup(x)})),
        x => `${x.group ? 0 : 1}-${x.identifier.toLowerCase()}`
    );

    return (
        <>
            <List divided relaxed styleName="list">
                {entries.map(data => (
                    <PrincipalListItem key={data.identifier}
                                       name={data.name}
                                       detail={data.detail}
                                       isGroup={data.group}
                                       onDelete={() => !disabled && handleDelete(data.identifier)}
                                       disabled={disabled} />
                ))}
                {pendingEntries.map(data => (
                    <PendingPrincipalListItem key={data.identifier} isGroup={data.group} />
                ))}
                {!value.length && (
                    <List.Item styleName="empty">
                        <Translate>
                            This list is currently empty
                        </Translate>
                    </List.Item>
                )}
            </List>
        </>
    );
};

PrincipalListField.propTypes = {
    value: PropTypes.arrayOf(PropTypes.string).isRequired,
    disabled: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
};

// eslint-disable-next-line react/prop-types
const PendingPrincipalListItem = ({isGroup}) => (
    <List.Item>
        <div styleName="item">
            <div styleName="icon">
                <Icon name={isGroup ? 'users' : 'user'} size="large" />
            </div>
            <div styleName="content">
                <List.Header>
                    {isGroup
                        ? <Translate>Unknown group</Translate>
                        : <Translate>Unknown user</Translate>}
                </List.Header>
            </div>
            <div styleName="loader">
                <Loader active inline size="small" />
            </div>
        </div>
    </List.Item>
);

// eslint-disable-next-line react/prop-types
const PrincipalListItem = ({isGroup, name, detail, onDelete, disabled}) => (
    <List.Item>
        <div styleName="item">
            <div styleName="icon">
                <Icon name={isGroup ? 'users' : 'user'} size="large" />
            </div>
            <div styleName="content">
                <List.Header>
                    {name}
                </List.Header>
                {detail && (
                    <List.Description>
                        {detail}
                    </List.Description>
                )}
            </div>
            <div>
                <Icon styleName="delete-button" name="remove" onClick={onDelete} size="large" disabled={disabled} />
            </div>
        </div>
    </List.Item>
);

export default React.memo(PrincipalListField);
