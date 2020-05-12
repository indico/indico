// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userSearchURL from 'indico-url:users.user_search';
import userSearchInfoURL from 'indico-url:users.user_search_info';
import groupSearchURL from 'indico-url:groups.group_search';

import _ from 'lodash';
import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  Divider,
  Dropdown,
  Form,
  Icon,
  Label,
  List,
  Message,
  Modal,
  Popup,
} from 'semantic-ui-react';
import {FORM_ERROR} from 'final-form';
import {Form as FinalForm} from 'react-final-form';
import Overridable from 'react-overridable';
import {FinalCheckbox, FinalInput, handleSubmitError} from 'indico/react/forms';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {useIndicoAxios} from 'indico/react/hooks';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {PrincipalType} from './util';

import './items.module.scss';
import './Search.module.scss';

const InitialFormValuesContext = React.createContext({});

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
    validateForm,
  } = config;

  /* eslint-disable react/prop-types */
  const FavoriteItem = ({name, detail, added, onAdd}) => (
    <Dropdown.Item
      disabled={added}
      styleName="favorite"
      style={{pointerEvents: 'all'}}
      onClick={e => {
        e.stopPropagation();
        onAdd();
      }}
    >
      <div styleName="item">
        <div styleName="icon">
          <Icon.Group size="large">
            <Icon name={resultIcon} />
            {added && <Icon name="check" color="green" corner />}
          </Icon.Group>
        </div>
        <div styleName="content">
          <List.Content>{name}</List.Content>
          {detail && (
            <List.Description>
              <small>{detail}</small>
            </List.Description>
          )}
        </div>
      </div>
    </Dropdown.Item>
  );

  const SearchForm = ({onSearch, favorites, isAdded, onAdd, single}) => {
    const initialFormValues = useContext(InitialFormValuesContext);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    return (
      <FinalForm
        onSubmit={onSearch}
        subscription={{submitting: true, hasValidationErrors: true, pristine: true}}
        validate={validateForm}
        initialValues={initialFormValues}
        initialValuesEqual={_.isEqual}
      >
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            {searchFields}
            <div styleName="search-buttons">
              <Button
                type="submit"
                icon="search"
                disabled={fprops.hasValidationErrors || fprops.pristine || fprops.submitting}
                loading={fprops.submitting}
                primary
                content={Translate.string('Search')}
              />
              {!_.isEmpty(favorites) && (
                <Dropdown
                  floating
                  labeled
                  text={Translate.string('Select favorite')}
                  disabled={fprops.submitting}
                  open={dropdownOpen}
                  onOpen={() => setDropdownOpen(true)}
                  onClose={() => setDropdownOpen(false)}
                >
                  <Dropdown.Menu>
                    {_.sortBy(Object.values(favorites), 'name').map(x => (
                      <FavoriteItem
                        key={x.identifier}
                        name={x.name}
                        detail={x.detail}
                        added={isAdded(x)}
                        onAdd={() => {
                          onAdd(x);
                          if (single) {
                            setDropdownOpen(false);
                          }
                        }}
                      />
                    ))}
                  </Dropdown.Menu>
                </Dropdown>
              )}
            </div>
          </Form>
        )}
      </FinalForm>
    );
  };

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
          <List.Content>{name}</List.Content>
          {detail && (
            <List.Description>
              <small>{detail}</small>
            </List.Description>
          )}
        </div>
        <div styleName="actions">
          {added ? (
            <Icon name="checkmark" size="large" color="green" />
          ) : (
            <Icon styleName="button" name="add" size="large" onClick={onAdd} />
          )}
        </div>
      </div>
    </List.Item>
  );

  const SearchResults = ({results, total, onAdd, isAdded, favorites}) =>
    total !== 0 ? (
      <>
        <Divider horizontal>{getResultsText(total)}</Divider>
        <List divided relaxed>
          {results.map(r => (
            <ResultItem
              key={r.identifier}
              name={r.name}
              detail={r.detail}
              added={isAdded(r)}
              favorite={favorites && favoriteKey ? r[favoriteKey] in favorites : false}
              onAdd={() => onAdd(r)}
            />
          ))}
        </List>
        {total > results.length && <Message info>{tooManyText}</Message>}
      </>
    ) : (
      <Divider horizontal>{noResultsText}</Divider>
    );

  const SearchContent = ({onAdd, isAdded, favorites, single}) => {
    const [result, setResult] = useState(null);

    const handleSearch = data => runSearch(data, setResult);
    return (
      <>
        <SearchForm
          onSearch={handleSearch}
          onAdd={onAdd}
          isAdded={isAdded}
          favorites={favorites}
          single={single}
        />
        {result !== null && (
          <SearchResults
            results={result.results}
            total={result.total}
            favorites={favorites}
            onAdd={onAdd}
            isAdded={isAdded}
          />
        )}
      </>
    );
  };
  /* eslint-enable react/prop-types */

  const Search = ({
    disabled,
    existing,
    onAddItems,
    favorites,
    triggerFactory,
    single,
    alwaysConfirm,
    onOpen,
    onClose,
  }) => {
    const [open, setOpen] = useState(false);
    const [staged, setStaged] = useState([]);

    const isAdded = ({identifier}) => {
      return existing.includes(identifier) || staged.some(x => x.identifier === identifier);
    };

    const handleAdd = item => {
      if (single && !alwaysConfirm) {
        onAddItems(item);
        setOpen(false);
      } else if (!isAdded(item)) {
        setStaged(prev => (single ? [item] : [...prev, item]));
      }
    };

    const handleAddButtonClick = () => {
      onAddItems(single ? staged[0] : staged);
      setStaged([]);
      setOpen(false);
    };

    const handleOpenClick = () => {
      if (disabled) {
        return;
      }
      setOpen(true);
      onOpen();
    };

    const handleClose = () => {
      setStaged([]);
      setOpen(false);
      onClose();
    };

    const trigger = triggerFactory ? (
      triggerFactory({disabled, onClick: handleOpenClick})
    ) : (
      <Button
        as="div"
        type="button"
        content={buttonTitle}
        disabled={disabled}
        onClick={handleOpenClick}
      />
    );

    const stopPropagation = evt => {
      // https://github.com/Semantic-Org/Semantic-UI-React/issues/3644
      evt.stopPropagation();
    };

    return (
      <Modal
        trigger={trigger}
        size="tiny"
        dimmer="inverted"
        centered={false}
        open={open}
        onClose={handleClose}
        onClick={stopPropagation}
        onFocus={stopPropagation}
        closeIcon
      >
        <Modal.Header>
          {modalTitle(single)}
          {!single && !!staged.length && (
            <>
              {' '}
              <Popup trigger={<Label circular>{staged.length}</Label>} position="bottom left">
                <List>
                  {_.sortBy(staged, 'name').map(x => (
                    <List.Item key={x.identifier}>{x.name}</List.Item>
                  ))}
                </List>
              </Popup>
            </>
          )}
          {single && alwaysConfirm && !!staged.length && (
            <>
              {' '}
              <Label circular>{staged[0].name}</Label>
            </>
          )}
        </Modal.Header>
        <Modal.Content>
          <SearchContent
            favorites={favorites}
            onAdd={handleAdd}
            isAdded={isAdded}
            single={single}
          />
        </Modal.Content>
        <Modal.Actions>
          {(!single || alwaysConfirm) && (
            <Button onClick={handleAddButtonClick} disabled={!staged.length} primary>
              <Translate>Confirm</Translate>
            </Button>
          )}
          <Button onClick={handleClose}>
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
    triggerFactory: PropTypes.func,
    single: PropTypes.bool,
    alwaysConfirm: PropTypes.bool,
    onOpen: PropTypes.func,
    onClose: PropTypes.func,
  };

  Search.defaultProps = {
    favorites: null,
    disabled: false,
    triggerFactory: null,
    single: false,
    alwaysConfirm: false,
    onOpen: () => {},
    onClose: () => {},
  };

  const component = React.memo(Search);
  component.displayName = componentName;
  return component;
};

const WithExternalsContext = React.createContext(false);

const UserSearchFields = () => {
  const withExternals = useContext(WithExternalsContext);

  const {data} = useIndicoAxios({
    url: userSearchInfoURL(),
    trigger: withExternals,
    forceDispatchEffect: () => withExternals,
    camelize: true,
  });

  const hasExternals = data && data.externalUsersAvailable;
  return (
    <>
      <FinalInput
        name="last_name"
        autoFocus
        noAutoComplete
        label={Translate.string('Family name')}
      />
      <FinalInput name="first_name" noAutoComplete label={Translate.string('Given name')} />
      <FinalInput
        name="email"
        type="email"
        noAutoComplete
        label={Translate.string('Email address')}
      />
      <FinalInput name="affiliation" noAutoComplete label={Translate.string('Affiliation')} />
      {hasExternals && (
        <FinalCheckbox
          name="external"
          label={Translate.string('Include users with no Indico account')}
        />
      )}
      <FinalCheckbox name="exact" label={Translate.string('Exact matches only')} />
    </>
  );
};

const InnerUserSearch = searchFactory({
  componentName: 'InnerUserSearch',
  buttonTitle: Translate.string('User'),
  modalTitle: single => (single ? Translate.string('Select user') : Translate.string('Add users')),
  resultIcon: 'user',
  favoriteKey: 'userId',
  searchFields: <UserSearchFields />,
  validateForm: values => {
    if (!values.first_name && !values.last_name && !values.email && !values.affiliation) {
      // no i18n needed, we do not show this error
      return {[FORM_ERROR]: 'No criteria specified'};
    }
  },
  runSearch: async (data, setResult) => {
    setResult(null);
    const values = _.fromPairs(Object.entries(data).filter(([, val]) => !!val));
    values.favorites_first = true;
    let response;
    try {
      response = await indicoAxios.get(userSearchURL(values));
    } catch (error) {
      return handleSubmitError(error);
    }
    const resultData = camelizeKeys(response.data);
    resultData.results = resultData.users.map(({identifier, id, fullName, email, affiliation}) => ({
      identifier,
      type: PrincipalType.user,
      userId: id,
      name: fullName,
      detail: affiliation ? `${email} (${affiliation})` : email,
    }));
    delete resultData.users;
    setResult(resultData);
  },
  tooManyText: Translate.string(
    'Your query matched too many users. Please try more specific search criteria.'
  ),
  noResultsText: Translate.string('No users found'),
  // eslint-disable-next-line react/display-name
  getResultsText: total => (
    <PluralTranslate count={total}>
      <Singular>1 user found</Singular>
      <Plural>
        <Param name="count" value={total} /> users found
      </Plural>
    </PluralTranslate>
  ),
});

export const DefaultUserSearch = ({withExternalUsers, initialFormValues, ...props}) => {
  if (!withExternalUsers) {
    // ignore form defaults for a field that's hidden
    delete initialFormValues.external;
  }
  return (
    <WithExternalsContext.Provider value={withExternalUsers}>
      <InitialFormValuesContext.Provider value={initialFormValues}>
        <InnerUserSearch {...props} />
      </InitialFormValuesContext.Provider>
    </WithExternalsContext.Provider>
  );
};

DefaultUserSearch.propTypes = {
  ...InnerUserSearch.propTypes,
  withExternalUsers: PropTypes.bool,
  initialFormValues: PropTypes.object,
};

DefaultUserSearch.defaultProps = {
  ...InnerUserSearch.defaultProps,
  withExternalUsers: false,
  initialFormValues: {},
};

export const UserSearch = Overridable.component('UserSearch', DefaultUserSearch);

export const GroupSearch = searchFactory({
  componentName: 'GroupSearch',
  buttonTitle: Translate.string('Group'),
  modalTitle: single =>
    single ? Translate.string('Select group') : Translate.string('Add groups'),
  resultIcon: 'users',
  searchFields: (
    <>
      <FinalInput
        name="name"
        autoFocus
        hideValidationError
        required
        noAutoComplete
        label={Translate.string('Group name')}
      />
      <FinalCheckbox name="exact" label={Translate.string('Exact matches only')} />
    </>
  ),
  runSearch: async (data, setResult) => {
    setResult(null);
    const values = _.fromPairs(Object.entries(data).filter(([, val]) => !!val));
    let response;
    try {
      response = await indicoAxios.get(groupSearchURL(values));
    } catch (error) {
      return handleSubmitError(error);
    }
    const resultData = camelizeKeys(response.data);
    resultData.results = resultData.groups.map(({identifier, name, provider, providerTitle}) => ({
      identifier,
      name,
      type: provider ? PrincipalType.multipassGroup : PrincipalType.localGroup,
      detail: providerTitle || null,
    }));
    delete resultData.groups;
    setResult(resultData);
  },
  tooManyText: Translate.string(
    'Your query matched too many groups. Please try more specific search criteria.'
  ),
  noResultsText: Translate.string('No groups found'),
  // eslint-disable-next-line react/display-name
  getResultsText: total => (
    <PluralTranslate count={total}>
      <Singular>1 group found</Singular>
      <Plural>
        <Param name="count" value={total} /> groups found
      </Plural>
    </PluralTranslate>
  ),
});
