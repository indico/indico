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

import userSearchURL from 'indico-url:users.user_search';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Divider, Form, Icon, List, Message} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {ReduxFormField, formatters, getChangedValues, handleSubmitError, validators as v} from 'indico/react/forms';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import './PrincipalListField.module.scss';


// eslint-disable-next-line react/prop-types
const UserSearchForm = ({onSearch}) => (
    <FinalForm onSubmit={onSearch} subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
        {(fprops) => (
            <Form onSubmit={fprops.handleSubmit}>
                <Field name="name" component={ReduxFormField} as="input"
                       format={formatters.trim} formatOnBlur
                       autoFocus hideValidationError
                       required validate={v.minLength(3)}
                       label={Translate.string('Name or Email')} />
                <Form.Button type="submit"
                             disabled={fprops.hasValidationErrors || fprops.pristine || fprops.submitting}
                             loading={fprops.submitting}
                             primary
                             content={Translate.string('Search')} />
            </Form>
        )}
    </FinalForm>
);


// eslint-disable-next-line react/prop-types
const UserItem = ({name, detail, added, onAdd}) => (
    <List.Item>
        <div styleName="item">
            <div styleName="icon">
                <Icon.Group size="large">
                    <Icon name="user" />
                    {detail.includes('pedro.ferreira@cern.ch') && <Icon name="star" color="yellow" corner />}
                </Icon.Group>
            </div>
            <div styleName="content">
                <List.Header>
                    {name}
                </List.Header>
                <List.Description>
                    <small>{detail}</small>
                </List.Description>
            </div>
            <div styleName="actions">
                {added
                    ? <Icon name="checkmark" size="large" color="green" />
                    : <Icon styleName="button" name="add" size="large" onClick={onAdd} />}
            </div>
        </div>
    </List.Item>
);


// eslint-disable-next-line react/prop-types
const UserSearchResults = ({users, total, onAdd, existing}) => (
    total !== 0 ? (
        <>
            <Divider horizontal>
                <PluralTranslate count={total}>
                    <Singular>
                        1 user found
                    </Singular>
                    <Plural>
                        <Param name="count" value={total} /> users found
                    </Plural>
                </PluralTranslate>
            </Divider>
            <List divided relaxed>
                {users.map(r => (
                    <UserItem key={r.identifier} name={r.name} detail={r.detail}
                              added={existing.includes(r.identifier)} onAdd={() => onAdd(r)} />
                ))}
            </List>
            {total > users.length && (
                <Message info>
                    <Translate>
                        Your query matched too many users. Please try more specific search criteria.
                    </Translate>
                </Message>
            )}
        </>
    ) : (
        <Divider horizontal>
            <Translate>No users found</Translate>
        </Divider>
    )
);


const convertUser = ({identifier, id, fullName, email, affiliation}) => ({
    identifier,
    userId: id,
    name: fullName,
    detail: affiliation ? `${email} (${affiliation})` : email,
    group: false,
});


const UserSearch = (props) => {
    const {existing, onAdd} = props;
    const [result, setResult] = useState(null);

    const handleSearch = async (data, form) => {
        setResult(null);
        const values = getChangedValues(data, form);
        if (values.name && values.name.includes('@')) {
            values.email = values.name;
            delete values.name;
        }
        values.favorites_first = true;
        let response;
        try {
            response = await indicoAxios.get(userSearchURL(values));
        } catch (error) {
            return handleSubmitError(error, {email: 'name'});
        }
        const resultData = camelizeKeys(response.data);
        resultData.users = resultData.users.map(convertUser);
        setResult(resultData);
    };

    return (
        <>
            <UserSearchForm onSearch={handleSearch} />
            {result !== null && (
                <UserSearchResults users={result.users} total={result.total}
                                   onAdd={onAdd} existing={existing} />
            )}
        </>
    );
};

UserSearch.propTypes = {
    onAdd: PropTypes.func.isRequired,
    existing: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default React.memo(UserSearch);
