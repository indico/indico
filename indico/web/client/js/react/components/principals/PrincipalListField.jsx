// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:core.principals';

import _ from 'lodash';
import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {Button, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {UserSearch, GroupSearch} from './Search';
import {PendingPrincipalListItem, PrincipalListItem} from './items';

import './PrincipalListField.module.scss';


/**
 * A field that lets the user select a list of users/groups.
 *
 * Setting the `readOnly` prop hides all UI elements used to modify
 * the entries, so it can be used to just display the current contents
 * outside editing mode.
 */
const PrincipalListField = (props) => {
    const {
        value, disabled, readOnly, onChange, onFocus, onBlur, withGroups, withExternalUsers, favoriteUsersController
    } = props;
    const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

    // keep track of details for each entry
    const [identifierMap, setIdentifierMap] = useState({});

    const isGroup = identifier => identifier.startsWith('Group:');
    const markTouched = () => {
        onFocus();
        onBlur();
    };
    const handleDelete = identifier => {
        onChange(value.filter(x => x !== identifier));
        markTouched();
    };
    const handleAddItems = data => {
        setIdentifierMap(prev => ({...prev, ..._.keyBy(data, 'identifier')}));
        onChange([...value, ...data.map(x => x.identifier)]);
        markTouched();
    };

    // fetch missing details
    useEffect(() => {
        const missingData = _.difference(value, Object.keys(identifierMap));
        if (!missingData.length) {
            return;
        }

        const source = indicoAxios.CancelToken.source();
        (async () => {
            let response;
            try {
                response = await indicoAxios.post(principalsURL(), {values: missingData}, {cancelToken: source.token});
            } catch (error) {
                handleAxiosError(error);
                return;
            }
            setIdentifierMap(prev => ({...prev, ...camelizeKeys(response.data)}));
        })();

        return () => {
            source.cancel();
        };
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
                                       isPendingUser={!data.group && data.userId === null}
                                       favorite={!data.group && data.userId in favoriteUsers}
                                       onDelete={() => !disabled && handleDelete(data.identifier)}
                                       onAddFavorite={() => !disabled && handleAddFavorite(data.userId)}
                                       onDelFavorite={() => !disabled && handleDelFavorite(data.userId)}
                                       disabled={disabled}
                                       readOnly={readOnly} />
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
            {!readOnly && (
                <Button.Group>
                    <Button icon="add" as="div" disabled />
                    <UserSearch existing={value} onAddItems={handleAddItems} favorites={favoriteUsers}
                                disabled={disabled} withExternalUsers={withExternalUsers} onOpen={onFocus}
                                onClose={onBlur} />
                    {withGroups && (
                        <GroupSearch existing={value} onAddItems={handleAddItems} disabled={disabled}
                                     onOpen={onFocus} onClose={onBlur} />
                    )}
                </Button.Group>
            )}
        </>
    );
};

PrincipalListField.propTypes = {
    value: PropTypes.arrayOf(PropTypes.string).isRequired,
    disabled: PropTypes.bool.isRequired,
    readOnly: PropTypes.bool,
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    favoriteUsersController: PropTypes.array.isRequired,
    withGroups: PropTypes.bool,
    withExternalUsers: PropTypes.bool,
};

PrincipalListField.defaultProps = {
    withGroups: false,
    withExternalUsers: false,
    readOnly: false,
};

export default React.memo(PrincipalListField);
