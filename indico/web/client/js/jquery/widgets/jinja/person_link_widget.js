// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userSearchTokenURL from 'indico-url:users.user_search_token';

import React, {useEffect, useState} from 'react';
import ReactDOM from 'react-dom';

import {WTFPersonLinkField} from 'indico/react/components/PersonLinkField';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

// TODO Remove all this once event creation is reactified and we don't need all these awful hacks
// anymore to make react and legacy jquery/wtforms components interact with each other...
const searchTokenCache = new Map();
// eslint-disable-next-line react/prop-types
function EventCreationWTFPersonLinkField({searchTokenSource, ...rest}) {
  const [userSearchDisabled, setUserSearchDisabled] = useState(true);
  const [categoryId, setCategoryId] = useState(undefined);
  useEffect(() => {
    const abortController = new AbortController();

    const listingField = document.querySelector('#event-creation-listing-checkbox');
    const categoryField = document.querySelector('#event-creation-category');
    const noCreationMessage = document.querySelector('#event-creation-message-container');

    const onChange = () => {
      // Get the selected category if available, or `undefined` if the event is being created
      // as unlisted or no category is selected. This also handles the listingField not existing
      // in case unlisted events are disabled.
      // The categoryField has an empty default value of `{}`, but when switching to unlisted and
      // back, we set its value to `null` instead of `{}` - don't ask me why! It seems to be related
      // to the initialCategory in the event creation dialog but I really do not feel like debugging
      // or changing this, since at some point that dialog gets rewritten in React anyway!
      // XXX It is kind of stupid to even do this for unlisted events, because letting a user create
      // unlisted events but restricting user search makes no sense whatsoever, as they will become
      // event manager, and thus be able to use the user search anyway. So we could actually just
      // provide a search token when the user is allowed to create unlisted events...
      const catId =
        listingField?.value === 'false' ? undefined : (JSON.parse(categoryField.value) ?? {}).id;
      // We use this ugly hack to check if event creation is possible in the category, since we do
      // not have access to the data from the event creation JS code... The only case where one can
      // have a category selected where they cannot create events is by using the event creation
      // button in such a category anyway, since it is not possible to select it via the category
      // picker.
      const eventCreationPossible = noCreationMessage.classList.contains('hidden');
      setUserSearchDisabled(catId === undefined || !eventCreationPossible);
      setCategoryId(catId);
    };

    listingField?.addEventListener('change', onChange, {signal: abortController.signal});
    categoryField.addEventListener('change', onChange, {signal: abortController.signal});
    onChange();

    return () => abortController.abort();
  }, []);

  rest.searchToken = async () => {
    let params, resp;
    if (searchTokenSource === 'event-creation-category') {
      params = {category_id: categoryId};
    } else {
      console.error(`Invalid search token source: ${searchTokenSource}`);
      return null;
    }
    const key = JSON.stringify(params);
    const cachedToken = searchTokenCache.get(key);
    if (cachedToken) {
      return cachedToken;
    }
    try {
      resp = await indicoAxios.get(userSearchTokenURL(params));
    } catch (error) {
      return handleAxiosError(error);
    }
    searchTokenCache.set(key, resp.data.token);
    return resp.data.token;
  };

  return <WTFPersonLinkField userSearchDisabled={userSearchDisabled} {...rest} />;
}

(function(global) {
  global.setupPersonLinkWidget = function setupPersonLinkWidget(options) {
    const {
      fieldId,
      eventId,
      roles,
      sessionUser,
      hasPredefinedAffiliations,
      allowCustomAffiliations,
      customPersonsMode,
      requiredPersonFields,
      defaultSearchExternal,
      nameFormat,
      extraParams,
      searchToken,
      searchTokenSource,
      ...rest
    } = options;
    const field = document.getElementById(fieldId);
    const persons = JSON.parse(field.value);
    const user = sessionUser &&
      sessionUser.id !== undefined && {
        title: sessionUser.title,
        userId: sessionUser.id,
        userIdentifier: sessionUser.identifier,
        avatarURL: sessionUser.avatarURL,
        firstName: sessionUser.firstName,
        lastName: sessionUser.lastName,
        affiliation: sessionUser.affiliation,
        affiliationId: sessionUser.affiliationId,
        affiliationMeta: sessionUser.affiliationMeta,
        email: sessionUser.email,
        address: sessionUser.address,
        phone: sessionUser.phone,
        type: sessionUser.type,
      };

    const WTFPersonLinkFieldComponent =
      searchTokenSource === 'event-creation-category'
        ? EventCreationWTFPersonLinkField
        : WTFPersonLinkField;

    ReactDOM.render(
      <WTFPersonLinkFieldComponent
        fieldId={fieldId}
        eventId={eventId}
        defaultValue={camelizeKeys(persons)}
        roles={roles || []}
        sessionUser={user}
        hasPredefinedAffiliations={hasPredefinedAffiliations}
        allowCustomAffiliations={allowCustomAffiliations}
        customPersonsMode={customPersonsMode}
        requiredPersonFields={requiredPersonFields}
        defaultSearchExternal={defaultSearchExternal}
        nameFormat={nameFormat}
        extraParams={camelizeKeys(extraParams)}
        searchToken={searchToken}
        searchTokenSource={searchTokenSource}
        {...rest}
      />,
      document.getElementById(`person-link-field-${fieldId}`)
    );
  };
})(window);
