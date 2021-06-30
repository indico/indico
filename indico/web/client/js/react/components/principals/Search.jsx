// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import groupSearchURL from 'indico-url:groups.group_search';
import eventPersonSearchURL from 'indico-url:persons.event_person_search';
import userSearchURL from 'indico-url:users.user_search';
import userSearchInfoURL from 'indico-url:users.user_search_info';

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useContext, useRef, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import Overridable from 'react-overridable';
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
  Image,
} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, handleSubmitError} from 'indico/react/forms';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
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
  const FavoriteItem = ({name, detail, added, onAdd, onRemove, avatarURL}) => {
    const avatar = avatarURL ? (
      <Image src={avatarURL} size="mini" avatar />
    ) : (
      <Icon name={resultIcon} />
    );

    const hasAvatarClass = avatarURL ? 'has-avatar' : '';

    return (
      <Dropdown.Item
        disabled={added}
        styleName="favorite"
        style={{pointerEvents: 'all'}}
        onClick={e => {
          e.stopPropagation();
          if (added) {
            onRemove();
          } else {
            onAdd();
          }
        }}
      >
        <div styleName="item">
          <div styleName="icon">
            <Icon.Group size="large">
              {avatar}
              {added && <Icon name="check" color="green" corner />}
            </Icon.Group>
          </div>
          <div styleName={`content ${hasAvatarClass}`}>
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
  };

  const SearchForm = ({onSearch, favorites, isAdded, onAdd, onRemove, single}) => {
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
                  scrolling
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
                        avatarURL={x.avatarURL}
                        onAdd={() => {
                          onAdd(x);
                          if (single) {
                            setDropdownOpen(false);
                          }
                        }}
                        onRemove={() => {
                          onRemove(x);
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

  const ResultItem = ({
    name,
    detail,
    added,
    favorite,
    onAdd,
    onRemove,
    existsInEvent,
    avatarURL,
  }) => {
    const avatar = avatarURL ? (
      <Image src={avatarURL} size="mini" avatar />
    ) : (
      <Icon name={resultIcon} />
    );

    const hasAvatarClass = avatarURL ? 'has-avatar' : '';

    return (
      <List.Item styleName="result-item" onClick={added ? onRemove : onAdd}>
        <div styleName="item">
          <div styleName="icon">
            <Icon.Group size="large">
              {avatar}
              {favorite && <Icon name="star" color="yellow" corner="bottom right" />}
              {existsInEvent && (
                <Popup
                  content={Translate.string('Person exists in event')}
                  trigger={<Icon name="ticket" styleName="event-person" corner="top right" />}
                  offset={[-15, 0]}
                  position="top left"
                />
              )}
            </Icon.Group>
          </div>
          <div styleName={`content ${hasAvatarClass}`}>
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
              <Icon styleName="button" name="add" size="large" />
            )}
          </div>
        </div>
      </List.Item>
    );
  };

  const SearchResults = ({
    results,
    total,
    loading,
    onAdd,
    onRemove,
    isAdded,
    favorites,
    // eslint-disable-next-line no-shadow
    getResultsText,
    ...rest
  }) => (
    <div styleName={`search-results ${loading ? 'disabled' : ''}`} {...rest}>
      {total !== 0 ? (
        <>
          <Divider horizontal>{getResultsText(total)}</Divider>
          <List styleName="list" divided relaxed>
            {results.map(r => (
              <ResultItem
                key={r.identifier}
                name={r.name}
                detail={r.detail}
                added={isAdded(r)}
                favorite={favorites && favoriteKey ? r[favoriteKey] in favorites : false}
                onAdd={() => onAdd(r)}
                onRemove={() => onRemove(r)}
                existsInEvent={r.existsInEvent}
                avatarURL={r.avatarURL}
              />
            ))}
          </List>
          {total > results.length && <Message info>{tooManyText}</Message>}
        </>
      ) : (
        <Divider horizontal>{noResultsText}</Divider>
      )}
    </div>
  );

  const SearchContent = ({
    onAdd,
    onRemove,
    isAdded,
    favorites,
    single,
    withEventPersons,
    eventId,
  }) => {
    const [loading, setLoading] = useState(false);
    const [result, _setResult] = useState(null);
    const lastResult = useRef(null);
    const pristine = useRef(true);
    const setResult = value => {
      lastResult.current = result;
      // pristine ignores initially unset values
      pristine.current = pristine.current && !value;
      _setResult(value);
    };
    const handleSearch = async data => {
      setLoading(true);
      try {
        await runSearch(data, setResult, withEventPersons, eventId);
      } finally {
        setLoading(false);
      }
    };
    const favoriteResults = favorites ? _.sortBy(Object.values(favorites), 'name') : [];
    const resultDisplay = result ||
      lastResult.current || {results: favoriteResults, total: favoriteResults.length};

    return (
      <div styleName="search-content">
        <div styleName="form">
          <SearchForm
            onSearch={handleSearch}
            onAdd={onAdd}
            onRemove={onRemove}
            isAdded={isAdded}
            favorites={favorites}
            single={single}
          />
        </div>
        {(!pristine.current || resultDisplay.total > 0) && (
          <SearchResults
            styleName="results"
            loading={loading}
            results={resultDisplay.results}
            total={resultDisplay.total}
            favorites={favorites}
            onAdd={onAdd}
            onRemove={onRemove}
            isAdded={isAdded}
            getResultsText={total =>
              resultDisplay.results === favoriteResults
                ? PluralTranslate.string('{total} favorite', '{total} favorites', total, {
                    total,
                  })
                : getResultsText(total)
            }
          />
        )}
      </div>
    );
  };

  const SearchStaged = ({single, staged, onRemove}) => {
    if (!staged || !staged.length) {
      return null;
    }

    if (single) {
      return (
        <Label circular styleName="staged-label">
          {staged[0].name}
          <Icon name="delete" onClick={() => onRemove(staged[0])} />
        </Label>
      );
    }

    return (
      <Popup
        trigger={
          <Label circular styleName="staged-label">
            {staged.length}
          </Label>
        }
        position="bottom left"
        hoverable
      >
        <List>
          {_.sortBy(staged, 'name').map(x => (
            <List.Item key={x.identifier}>
              <div styleName="staged-list-item">
                {x.name}
                <Icon styleName="button" name="delete" onClick={() => onRemove(x)} />
              </div>
            </List.Item>
          ))}
        </List>
      </Popup>
    );
  };
  /* eslint-enable react/prop-types */

  const Search = ({
    disabled,
    existing,
    onAddItems,
    favorites,
    triggerFactory,
    defaultOpen,
    single,
    alwaysConfirm,
    onOpen,
    onClose,
    withEventPersons,
    eventId,
  }) => {
    const [open, setOpen] = useState(defaultOpen);
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

    const handleRemove = item => {
      setStaged(prev => prev.filter(it => it.identifier !== item.identifier));
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

    let trigger = null;
    if (!defaultOpen) {
      trigger = triggerFactory ? (
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
    }

    const stopPropagation = evt => {
      // https://github.com/Semantic-Org/Semantic-UI-React/issues/3644
      evt.stopPropagation();
    };

    return (
      <Modal
        trigger={trigger}
        dimmer="inverted"
        centered={false}
        open={open}
        onClose={handleClose}
        onClick={stopPropagation}
        onFocus={stopPropagation}
        closeIcon
      >
        <Modal.Header styleName="header">
          {modalTitle(single)}{' '}
          {(!single || alwaysConfirm) && (
            <SearchStaged
              single={single}
              alwaysConfirm={alwaysConfirm}
              staged={staged}
              onRemove={handleRemove}
            />
          )}
        </Modal.Header>
        <Modal.Content>
          <SearchContent
            favorites={favorites}
            onAdd={handleAdd}
            onRemove={handleRemove}
            isAdded={isAdded}
            single={single}
            withEventPersons={withEventPersons}
            eventId={eventId}
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
    defaultOpen: PropTypes.bool,
    single: PropTypes.bool,
    alwaysConfirm: PropTypes.bool,
    onOpen: PropTypes.func,
    onClose: PropTypes.func,
    withEventPersons: PropTypes.bool,
    eventId: PropTypes.number,
  };

  Search.defaultProps = {
    favorites: null,
    disabled: false,
    triggerFactory: null,
    defaultOpen: false,
    single: false,
    alwaysConfirm: false,
    onOpen: () => {},
    onClose: () => {},
    withEventPersons: false,
    eventId: null,
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
      <FinalInput name="email" noAutoComplete label={Translate.string('Email address')} />
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
  runSearch: async (data, setResult, withEventPersons, eventId) => {
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
    resultData.results = resultData.users.map(
      ({identifier, id, fullName, email, affiliation, firstName, lastName, avatarURL}) => ({
        identifier,
        type: PrincipalType.user,
        userId: id,
        id,
        name: fullName,
        detail: affiliation ? `${email} (${affiliation})` : email,
        firstName,
        lastName,
        existsInEvent: false,
        email,
        affiliation,
        avatarURL,
      })
    );
    delete resultData.users;
    if (withEventPersons) {
      let epResponse;
      try {
        epResponse = await indicoAxios.get(eventPersonSearchURL({...values, event_id: eventId}));
      } catch (error) {
        return handleSubmitError(error);
      }
      const epResultData = camelizeKeys(epResponse.data);
      epResultData.results = epResultData.users.map(
        ({identifier, id, fullName, email, affiliation, firstName, lastName, userIdentifier}) => ({
          identifier,
          type: PrincipalType.eventPerson,
          id,
          name: fullName,
          detail: affiliation ? `${email} (${affiliation})` : email,
          firstName,
          lastName,
          existsInEvent: true,
          email,
          affiliation,
          userIdentifier,
        })
      );
      const epResults = [];
      epResultData.results.forEach(item => {
        if (item.userIdentifier !== undefined) {
          const index = resultData.results.findIndex(e => e.identifier === item.userIdentifier);
          if (index >= 0) {
            resultData.results[index].existsInEvent = true;
            return;
          }
        }
        epResults.push(item);
      });
      resultData.results = [...epResults, ...resultData.results];
      resultData.total += epResults.length;
    }
    setResult(resultData);
  },
  tooManyText: Translate.string(
    'Your query matched too many users. Please try more specific search criteria.'
  ),
  noResultsText: Translate.string('No users found'),
  // eslint-disable-next-line react/display-name
  getResultsText: total => (
    <PluralTranslate count={total}>
      <Singular>
        <Param name="count" value={total} /> user found
      </Singular>
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

/**
 * Like UserSearch, but lazy-loads the favorite users on demand.
 */
export function LazyUserSearch(props) {
  const [favorites, [, , loadFavorites]] = useFavoriteUsers(null, true);
  return <UserSearch favorites={favorites} onOpen={loadFavorites} {...props} />;
}

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
      provider,
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
      <Singular>
        <Param name="count" value={total} /> group found
      </Singular>
      <Plural>
        <Param name="count" value={total} /> groups found
      </Plural>
    </PluralTranslate>
  ),
});
