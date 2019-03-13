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
import {Button, Divider, Dropdown, Form, Icon, Label, List, Message, Modal, Popup} from 'semantic-ui-react';
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
        buttonTitle,
        modalTitle,
        searchFields,
        resultIcon,
        getResultsText,
        tooManyText,
        favoriteKey,
        noResultsText,
        runSearch,
    } = config;

    // eslint-disable-next-line react/prop-types
    const FavoriteItem = ({name, detail, added, onAdd}) => (
        <Dropdown.Item disabled={added} styleName="favorite"
                       style={{pointerEvents: 'all'}}
                       onClick={e => {
                           e.stopPropagation();
                           onAdd();
                       }}>
            <div styleName="item">
                <div styleName="icon">
                    <Icon.Group size="large">
                        <Icon name={resultIcon} />
                        {added && <Icon name="check" color="green" corner />}
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
            </div>
        </Dropdown.Item>
    );

    // eslint-disable-next-line react/prop-types
    const SearchForm = ({onSearch, favorites, isAdded, onAdd}) => (
        <FinalForm onSubmit={onSearch} subscription={{submitting: true, hasValidationErrors: true, pristine: true}}>
            {(fprops) => (
                <Form onSubmit={fprops.handleSubmit}>
                    {searchFields}
                    <Button type="submit"
                            disabled={fprops.hasValidationErrors || fprops.pristine || fprops.submitting}
                            loading={fprops.submitting}
                            primary
                            content={Translate.string('Search')} />
                    {favorites && (
                        <Dropdown text={Translate.string('Select favorite')}
                                  icon="star" floating labeled button className="icon">
                            <Dropdown.Menu>
                                {_.sortBy(Object.values(favorites), 'name').map(x => (
                                    <FavoriteItem key={x.identifier} name={x.name} detail={x.detail}
                                                  added={isAdded(x)} onAdd={() => onAdd(x)} />
                                ))}
                            </Dropdown.Menu>
                        </Dropdown>
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
    const SearchResults = ({results, total, onAdd, isAdded, favorites}) => (
        total !== 0 ? (
            <>
                <Divider horizontal>
                    {getResultsText(total)}
                </Divider>
                <List divided relaxed>
                    {results.map(r => (
                        <ResultItem key={r.identifier} name={r.name} detail={r.detail}
                                    added={isAdded(r)}
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

    // eslint-disable-next-line react/prop-types
    const SearchContent = ({onAdd, isAdded, favorites}) => {
        const [result, setResult] = useState(null);

        const handleSearch = (data, form) => runSearch(data, form, setResult);
        return (
            <>
                <SearchForm onSearch={handleSearch} onAdd={onAdd} isAdded={isAdded} favorites={favorites} />
                {result !== null && (
                    <SearchResults results={result.results} total={result.total} favorites={favorites}
                                   onAdd={onAdd} isAdded={isAdded} />
                )}
            </>
        );
    };

    const Search = ({disabled, existing, onAddItems, favorites}) => {
        const [open, setOpen] = useState(false);
        const [staged, setStaged] = useState([]);

        const isAdded = ({identifier}) => {
            return existing.includes(identifier) || staged.some(x => x.identifier === identifier);
        };

        const handleAdd = item => {
            if (!isAdded(item)) {
                setStaged(prev => [...prev, item]);
            }
        };

        const handleAddButtonClick = () => {
            onAddItems(staged);
            setStaged([]);
            setOpen(false);
        };

        const handleCancelButtonClick = () => {
            setStaged([]);
            setOpen(false);
        };

        const trigger = (
            <Button type="button"
                    content={buttonTitle}
                    disabled={disabled}
                    onClick={() => setOpen(true)} />
        );
        return (
            <Modal trigger={trigger}
                   size="tiny"
                   dimmer="inverted"
                   centered={false}
                   open={open}
                   onClose={() => setOpen(false)}
                   closeIcon>
                <Modal.Header>
                    {modalTitle}
                    {!!staged.length && (
                        <>
                            {' '}
                            <Popup trigger={<Label circular>{staged.length}</Label>}
                                   position="bottom left">
                                <List>
                                    {_.sortBy(staged, 'name').map(x => (
                                        <List.Item key={x.identifier}>{x.name}</List.Item>
                                    ))}
                                </List>
                            </Popup>
                        </>
                    )}
                </Modal.Header>
                <Modal.Content>
                    <SearchContent favorites={favorites} onAdd={handleAdd} isAdded={isAdded} />
                </Modal.Content>
                <Modal.Actions>
                    <Button onClick={handleAddButtonClick} disabled={!staged.length} primary>
                        <Translate>Confirm</Translate>
                    </Button>
                    <Button onClick={handleCancelButtonClick}>
                        <Translate>Cancel</Translate>
                    </Button>
                </Modal.Actions>
            </Modal>
        );
    };

    Search.propTypes = {
        onAddItems: PropTypes.func.isRequired,
        existing: PropTypes.arrayOf(PropTypes.string).isRequired,
        disabled: PropTypes.bool,
        favorites: PropTypes.object,
    };

    Search.defaultProps = {
        favorites: null,
        disabled: false,
    };

    const component = React.memo(Search);
    component.displayName = componentName;
    return component;
};


export const UserSearch = searchFactory({
    componentName: 'UserSearch',
    buttonTitle: Translate.string('User'),
    modalTitle: Translate.string('Add users'),
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
    buttonTitle: Translate.string('Group'),
    modalTitle: Translate.string('Add groups'),
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
