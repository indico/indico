// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
import React, {useContext, useEffect, useMemo, useRef, useState} from 'react';
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

  const SearchForm = ({onSearch, favoritesController, isAdded, onAdd, onRemove, single}) => {
    const initialFormValues = useContext(InitialFormValuesContext);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const favorites = favoritesController?.[0] ?? [];
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

  const FavoriteControls = ({favorite, onAddFavorite, onDelFavorite}) =>
    favorite ? (
      <Icon
        styleName="button favorite active"
        name="star"
        size="large"
        title={Translate.string('Remove from favorites')}
        onClick={evt => {
          evt.stopPropagation();
          onDelFavorite();
        }}
      />
    ) : (
      <Icon
        styleName="button favorite"
        name="star outline"
        size="large"
        title={Translate.string('Add to favorites')}
        onClick={evt => {
          evt.stopPropagation();
          onAddFavorite();
        }}
      />
    );

  const ResultItem = ({
    name,
    detail,
    added,
    favorite,
    onAdd,
    onRemove,
    onAddFavorite,
    onDelFavorite,
    existsInEvent,
    external,
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
              {external && (
                <Popup
                  content={Translate.string('Person does not have an Indico account yet')}
                  trigger={<Icon name="external" styleName="event-person" corner="top right" />}
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
            {!external && onAddFavorite && onDelFavorite && (
              <FavoriteControls
                onAddFavorite={onAddFavorite}
                onDelFavorite={onDelFavorite}
                favorite={favorite}
              />
            )}
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
    pristine,
    onAdd,
    onRemove,
    onEnterManually,
    isAdded,
    favoritesController,
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
                favorite={
                  favoritesController && favoriteKey
                    ? r[favoriteKey] in favoritesController[0]
                    : false
                }
                onAddFavorite={
                  favoritesController && r.type === 'user' && r.userId !== null
                    ? () => favoritesController[1][0](r.userId)
                    : null
                }
                onDelFavorite={
                  favoritesController && r.type === 'user' && r.userId !== null
                    ? () => favoritesController[1][1](r.userId)
                    : null
                }
                onAdd={() => onAdd(r)}
                onRemove={() => onRemove(r)}
                existsInEvent={r.existsInEvent}
                external={r.type === 'user' && r.userId === null}
                avatarURL={r.avatarURL}
              />
            ))}
          </List>
          {total > results.length && <Message info>{tooManyText}</Message>}
        </>
      ) : (
        <Divider horizontal>{noResultsText}</Divider>
      )}
      {onEnterManually && !pristine && (
        <Message>
          <Translate as={Message.Header}>I could not find the right person</Translate>
          <Translate as={Message.Content}>
            If nobody on the search results corresponds to the person you were looking for, you can{' '}
            <Param name="enterManuallyLink" wrapper={<a onClick={onEnterManually} />}>
              add them manually
            </Param>
            .
          </Translate>
        </Message>
      )}
    </div>
  );

  const SearchContent = ({
    onAdd,
    onRemove,
    onEnterManually,
    isAdded,
    favoritesController,
    single,
    withEventPersons,
    eventId,
  }) => {
    const [loading, setLoading] = useState(false);
    const [result, _setResult] = useState(null);
    const [initialFavoritesResults, setInitialFavoritesResults] = useState([]);
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
    const favoriteResults = useMemo(
      () => (favoritesController ? _.sortBy(Object.values(favoritesController[0]), 'name') : []),
      [favoritesController]
    );
    useEffect(() => {
      // favoriteResults is empty during the first render, so as soon as we have a value for it
      // we shove it into local state so later changes to the favorite (ie removing a favorite)
      // no longer affects that list, since we don't want a user that's removed from favorites
      // immediately disappear from the visible list (in case someone misclicks and wanted to
      // select the user instead)
      if (favoriteResults.length && !initialFavoritesResults.length) {
        setInitialFavoritesResults(favoriteResults);
      }
    }, [favoriteResults, initialFavoritesResults]);
    const resultDisplay = result ||
      lastResult.current || {
        results: initialFavoritesResults,
        total: initialFavoritesResults.length,
      };

    return (
      <div styleName="search-content">
        <div styleName="form">
          <SearchForm
            onSearch={handleSearch}
            onAdd={onAdd}
            onRemove={onRemove}
            isAdded={isAdded}
            favoritesController={favoritesController}
            single={single}
          />
        </div>
        {(!pristine.current || resultDisplay.total > 0) && (
          <SearchResults
            styleName="results"
            loading={loading}
            pristine={pristine.current}
            results={resultDisplay.results}
            total={resultDisplay.total}
            favoritesController={favoritesController}
            onAdd={onAdd}
            onRemove={onRemove}
            onEnterManually={onEnterManually}
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
    favoritesController,
    triggerFactory,
    defaultOpen,
    single,
    alwaysConfirm,
    onOpen,
    onClose,
    onEnterManually,
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

    const handleEnterManually = () => {
      setOpen(false);
      onEnterManually();
    };
    const handleAddButtonClick = () => {
      onAddItems(single ? staged[0] : staged);
      setStaged([]);
      setOpen(false);
    };

    const handleOpenClick = evt => {
      evt.preventDefault();
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
            favoritesController={favoritesController}
            onAdd={handleAdd}
            onRemove={handleRemove}
            onEnterManually={onEnterManually ? handleEnterManually : null}
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
    favoritesController: PropTypes.array,
    triggerFactory: PropTypes.func,
    defaultOpen: PropTypes.bool,
    single: PropTypes.bool,
    alwaysConfirm: PropTypes.bool,
    onOpen: PropTypes.func,
    onClose: PropTypes.func,
    onEnterManually: PropTypes.func,
    withEventPersons: PropTypes.bool,
    eventId: PropTypes.number,
  };

  Search.defaultProps = {
    favoritesController: null,
    disabled: false,
    triggerFactory: null,
    defaultOpen: false,
    single: false,
    alwaysConfirm: false,
    onOpen: () => {},
    onClose: () => {},
    onEnterManually: null,
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

  const {data} = useIndicoAxios(userSearchInfoURL(), {
    camelize: true,
    manual: !withExternals,
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
  modalTitle: single =>
    single ? Translate.string('Select user') : Translate.string('Select users'),
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
      ({
        identifier,
        id,
        title,
        fullName,
        email,
        affiliation,
        affiliationId,
        affiliationMeta,
        firstName,
        lastName,
        avatarURL,
      }) => ({
        identifier,
        type: PrincipalType.user,
        userId: id,
        id,
        title,
        name: fullName,
        detail: affiliation ? `${email} (${affiliation})` : email,
        firstName,
        lastName,
        existsInEvent: false,
        email,
        affiliation,
        affiliationId,
        affiliationMeta,
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
        ({
          identifier,
          id,
          title,
          name,
          email,
          affiliation,
          affiliationId,
          affiliationMeta,
          firstName,
          lastName,
          userIdentifier,
        }) => ({
          identifier,
          type: PrincipalType.eventPerson,
          id,
          personId: id,
          title,
          name,
          detail: affiliation ? `${email} (${affiliation})` : email,
          firstName,
          lastName,
          existsInEvent: true,
          email,
          affiliation,
          affiliationId,
          affiliationMeta,
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
    // eslint-disable-next-line react/destructuring-assignment
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
  const favoriteUsersController = useFavoriteUsers(null, true);
  const [, [, , loadFavorites]] = favoriteUsersController;
  return (
    <UserSearch favoritesController={favoriteUsersController} onOpen={loadFavorites} {...props} />
  );
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
