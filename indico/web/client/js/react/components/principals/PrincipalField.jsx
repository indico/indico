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

import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import {Icon, List} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {UserSearch} from './Search';
import {EmptyPrincipalListItem, PendingPrincipalListItem, PrincipalListItem} from './items';

import './items.module.scss';


/**
 * A field that lets the user select a user.
 */
const PrincipalField = (props) => {
    const {value, disabled, required, onChange, onFocus, onBlur, favoriteUsersController, withExternalUsers} = props;
    const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

    const [details, setDetails] = useState(null);

    const markTouched = () => {
        onFocus();
        onBlur();
    };

    useEffect(() => {
        if (!value) {
            if (details) {
                // clear old details
                setDetails(null);
            }
            return;
        }
        if (details && details.identifier === value) {
            // nothing to do
            return;
        }
        const source = indicoAxios.CancelToken.source();
        (async () => {
            let response;
            try {
                response = await indicoAxios.post(principalsURL(), {values: [value]}, {cancelToken: source.token});
            } catch (error) {
                handleAxiosError(error);
                return;
            }
            setDetails(camelizeKeys(response.data[value]));
        })();

        return () => {
            source.cancel();
        };
    }, [details, value]);

    const handleAddItem = principal => {
        onChange(principal.identifier);
        markTouched();
    };
    const handleClear = () => {
        onChange(null);
        markTouched();
    };

    const searchTrigger = triggerProps => (
        <Icon styleName="button" name="search" size="large" {...triggerProps} />
    );
    const userSearch = (
        <UserSearch triggerFactory={searchTrigger}
                    existing={value ? [value] : []}
                    onAddItems={handleAddItem}
                    onOpen={onFocus}
                    onClose={onBlur}
                    favorites={favoriteUsers}
                    disabled={disabled}
                    withExternalUsers={withExternalUsers}
                    single />
    );

    return (
        <div className="ui input">
            <div className="fake-input">
                <List relaxed>
                    {!value ? (
                        <EmptyPrincipalListItem search={userSearch} />
                    ) : (
                        details ? (
                            <PrincipalListItem name={details.name}
                                               detail={details.detail}
                                               favorite={details.userId in favoriteUsers}
                                               isPendingUser={details.userId === null}
                                               canDelete={!required}
                                               onDelete={() => !disabled && handleClear()}
                                               onAddFavorite={() => !disabled && handleAddFavorite(details.userId)}
                                               onDelFavorite={() => !disabled && handleDelFavorite(details.userId)}
                                               disabled={disabled}
                                               search={userSearch} />
                        ) : (
                            <PendingPrincipalListItem />
                        )
                    )}
                </List>
            </div>
        </div>
    );
};

PrincipalField.propTypes = {
    value: PropTypes.string,
    required: PropTypes.bool,
    disabled: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    favoriteUsersController: PropTypes.array.isRequired,
    withExternalUsers: PropTypes.bool,
};

PrincipalField.defaultProps = {
    value: null,
    required: false,
    withExternalUsers: false,
};

export default React.memo(PrincipalField);
