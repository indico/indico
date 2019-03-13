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
import groupSearchURL from 'indico-url:groups.group_search';

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Divider, Dropdown, Form, Icon, List, Message} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {
    ReduxCheckboxField, ReduxFormField, formatters, getChangedValues, handleSubmitError, validators as v
} from 'indico/react/forms';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import './PrincipalListField.module.scss';


const searchFactory = config => {
    const {
        componentName,
        searchFields,
        resultIcon,
        getResultsText,
        tooManyText,
        favoriteKey,
        noResultsText,
        runSearch,
    } = config;

    // eslint-disable-next-line react/prop-types
    const SearchForm = ({onSearch, favorites, onAdd}) => (
        <FinalForm onSubmit={onSearch} subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
            {(fprops) => (
                <Form onSubmit={fprops.handleSubmit}>
                    {searchFields}
                    <Button type="submit"
                            disabled={fprops.hasValidationErrors || fprops.pristine || fprops.submitting}
                            loading={fprops.submitting}
                            primary
                            content={Translate.string('Search')} />
                    {!!Object.keys(favorites).length && (
                        <Dropdown text={Translate.string('Add favorite')}
                                  icon="star" floating labeled button className="icon"
                                  selectOnBlur={false}
                                  options={_.sortBy(Object.values(favorites), 'name').map(x => ({
                                      key: x.identifier,
                                      value: x.userId,
                                      text: x.name,
                                  }))}
                                  onChange={(e, {value}) => {
                                      onAdd(favorites[value]);
                                  }} />
                    )}
                </Form>
            )}
        </FinalForm>
    );

    // eslint-disable-next-line react/prop-types
    const ResultItem = ({name, detail, added, favorite, onAdd}) => (
        <List.Item>
            <div styleName="item">
                <div styleName="icon">
                    <Icon.Group size="large">
                        <Icon name={resultIcon} />
                        {favorite && <Icon name="star" color="yellow" corner />}
                    </Icon.Group>
                </div>
                <div styleName="content">
                    <List.Content>
                        {name}
                    </List.Content>
                    {detail && (
                        <List.Description>
                            <small>{detail}</small>
                        </List.Description>
                    )}
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
    const SearchResults = ({results, total, onAdd, existing, favorites}) => (
        total !== 0 ? (
            <>
                <Divider horizontal>
                    {getResultsText(total)}
                </Divider>
                <List divided relaxed>
                    {results.map(r => (
                        <ResultItem key={r.identifier} name={r.name} detail={r.detail}
                                    added={existing.includes(r.identifier)}
                                    favorite={(favorites && favoriteKey) ? (r[favoriteKey] in favorites) : false}
                                    onAdd={() => onAdd(r)} />
                    ))}
                </List>
                {total > results.length && (
                    <Message info>
                        {tooManyText}
                    </Message>
                )}
            </>
        ) : (
            <Divider horizontal>
                {noResultsText}
            </Divider>
        )
    );

    const Search = (props) => {
        const {existing, onAdd, favorites} = props;
        const [result, setResult] = useState(null);
        const handleSearch = (data, form) => runSearch(data, form, setResult);
        const availableFavorites = _.fromPairs(
            Object.entries(favorites || {}).filter(([, x]) => !existing.includes(x.identifier))
        );
        return (
            <>
                <SearchForm onSearch={handleSearch} favorites={availableFavorites} onAdd={onAdd} />
                {result !== null && (
                    <SearchResults results={result.results} total={result.total} favorites={favorites}
                                   onAdd={onAdd} existing={existing} />
                )}
            </>
        );
    };

    Search.propTypes = {
        onAdd: PropTypes.func.isRequired,
        existing: PropTypes.arrayOf(PropTypes.string).isRequired,
        favorites: PropTypes.object,
    };

    Search.defaultProps = {
        favorites: null,
    };

    const component = React.memo(Search);
    component.displayName = componentName;
    return component;
};


export const UserSearch = searchFactory({
    componentName: 'UserSearch',
    resultIcon: 'user',
    favoriteKey: 'userId',
    searchFields: (
        <Field name="name" component={ReduxFormField} as="input"
               format={formatters.trim} formatOnBlur
               autoFocus hideValidationError
               required validate={v.minLength(3)}
               label={Translate.string('Name or Email')} />
    ),
    runSearch: async (data, form, setResult) => {
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
        resultData.results = resultData.users.map(({identifier, id, fullName, email, affiliation}) => ({
            identifier,
            userId: id,
            name: fullName,
            detail: affiliation ? `${email} (${affiliation})` : email,
            group: false,
        }));
        delete resultData.users;
        setResult(resultData);
    },
    tooManyText: Translate.string('Your query matched too many users. Please try more specific search criteria.'),
    noResultsText: Translate.string('No users found'),
    // eslint-disable-next-line react/display-name
    getResultsText: total => (
        <PluralTranslate count={total}>
            <Singular>
                1 user found
            </Singular>
            <Plural>
                <Param name="count" value={total} /> users found
            </Plural>
        </PluralTranslate>
    ),
});


export const GroupSearch = searchFactory({
    componentName: 'GroupSearch',
    resultIcon: 'users',
    searchFields: (
        <>
            <Field name="name" component={ReduxFormField} as="input"
                   format={formatters.trim} formatOnBlur
                   autoFocus hideValidationError
                   required validate={v.required}
                   label={Translate.string('Group name')} />
            <Field name="exact" component={ReduxCheckboxField}
                   componentLabel={Translate.string('Exact matches only')} />
        </>
    ),
    runSearch: async (data, form, setResult) => {
        setResult(null);
        const values = getChangedValues(data, form);
        let response;
        try {
            response = await indicoAxios.get(groupSearchURL(values));
        } catch (error) {
            return handleSubmitError(error);
        }
        const resultData = camelizeKeys(response.data);
        resultData.results = resultData.groups.map(({identifier, name, providerTitle}) => ({
            identifier,
            name,
            detail: providerTitle || null,
            group: true,
        }));
        delete resultData.groups;
        setResult(resultData);
    },
    tooManyText: Translate.string('Your query matched too many groups. Please try more specific search criteria.'),
    noResultsText: Translate.string('No groups found'),
    // eslint-disable-next-line react/display-name
    getResultsText: total => (
        <PluralTranslate count={total}>
            <Singular>
                1 group found
            </Singular>
            <Plural>
                <Param name="count" value={total} /> groups found
            </Plural>
        </PluralTranslate>
    ),
});
