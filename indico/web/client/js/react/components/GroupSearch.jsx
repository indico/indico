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

import groupSearchURL from 'indico-url:groups.group_search';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Divider, Form, Icon, List, Message} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {
    ReduxCheckboxField, ReduxFormField, formatters, getChangedValues, handleSubmitError, validators as v
} from 'indico/react/forms';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import './PrincipalListField.module.scss';


// eslint-disable-next-line react/prop-types
const GroupSearchForm = ({onSearch}) => (
    <FinalForm onSubmit={onSearch} subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
        {(fprops) => (
            <Form onSubmit={fprops.handleSubmit}>
                <Field name="name" component={ReduxFormField} as="input"
                       format={formatters.trim} formatOnBlur
                       autoFocus hideValidationError
                       required validate={v.required}
                       label={Translate.string('Group name')} />
                <Field name="exact" component={ReduxCheckboxField}
                       componentLabel={Translate.string('Exact matches only')} />
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
const GroupItem = ({name, detail, added, onAdd}) => (
    <List.Item>
        <div styleName="item">
            <div styleName="icon">
                <Icon name="users" size="large" />
            </div>
            <div styleName="content">
                <List.Header>
                    {name}
                </List.Header>
                {detail && (
                    <List.Description>
                        <small>{detail}</small>
                    </List.Description>
                )}
            </div>
            <div>
                {added
                    ? <Icon name="checkmark" size="large" color="green" />
                    : <Icon styleName="button" name="add" size="large" onClick={onAdd} />}
            </div>
        </div>
    </List.Item>
);


// eslint-disable-next-line react/prop-types
const GroupSearchResults = ({groups, total, onAdd, existing}) => (
    total !== 0 ? (
        <>
            <Divider horizontal>
                <PluralTranslate count={total}>
                    <Singular>
                        1 group found
                    </Singular>
                    <Plural>
                        <Param name="count" value={total} /> groups found
                    </Plural>
                </PluralTranslate>
            </Divider>
            <List divided relaxed>
                {groups.map(r => (
                    <GroupItem key={r.identifier} name={r.name} detail={r.detail}
                               added={existing.includes(r.identifier)} onAdd={() => onAdd(r)} />
                ))}
            </List>
            {total > groups.length && (
                <Message info>
                    <Translate>
                        Your query matched too many groups. Please try more specific search criteria.
                    </Translate>
                </Message>
            )}
        </>
    ) : (
        <Divider horizontal>
            <Translate>No groups found</Translate>
        </Divider>
    )
);


const convertGroup = ({identifier, name, providerTitle}) => ({
    identifier,
    name,
    detail: providerTitle || null,
    group: true,
});


const GroupSearch = (props) => {
    const {existing, onAdd} = props;
    const [result, setResult] = useState(null);

    const handleSearch = async (data, form) => {
        setResult(null);
        const values = getChangedValues(data, form);
        let response;
        try {
            response = await indicoAxios.get(groupSearchURL(values));
        } catch (error) {
            return handleSubmitError(error);
        }
        const resultData = camelizeKeys(response.data);
        resultData.groups = resultData.groups.map(convertGroup);
        setResult(resultData);
    };

    return (
        <>
            <GroupSearchForm onSearch={handleSearch} />
            {result !== null && (
                <GroupSearchResults groups={result.groups} total={result.total}
                                    onAdd={onAdd} existing={existing} />
            )}
        </>
    );
};

GroupSearch.propTypes = {
    onAdd: PropTypes.func.isRequired,
    existing: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default React.memo(GroupSearch);
