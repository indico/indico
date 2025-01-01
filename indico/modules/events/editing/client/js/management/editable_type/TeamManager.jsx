// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:event_editing.api_editable_type_principals';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Loader, Message} from 'semantic-ui-react';

import {FinalPrincipalList} from 'indico/react/components';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';
import {indicoAxios} from 'indico/utils/axios';

export default function TeamManager({editableType, onClose}) {
  const eventId = useNumericParam('event_id');
  const favoriteUsersController = useFavoriteUsers();

  const {data: principals, loading: isLoadingPrincipals} = useIndicoAxios(
    principalsURL({event_id: eventId, type: editableType})
  );

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    try {
      await indicoAxios.post(principalsURL({event_id: eventId, type: editableType}), changedValues);
    } catch (error) {
      return handleSubmitError(error);
    }
    onClose();
  };

  if (isLoadingPrincipals) {
    return <Loader active />;
  } else if (!principals) {
    return null;
  }

  return (
    <FinalModalForm
      id="team-manager"
      size="small"
      onSubmit={handleSubmit}
      onClose={onClose}
      header={Translate.string('Set editors')}
      initialValues={{principals}}
      initialValuesEqual={_.isEqual}
      unloadPrompt
      unloadPromptRouter
    >
      <Message>
        <FinalPrincipalList
          name="principals"
          withEventRoles
          withCategoryRoles
          favoriteUsersController={favoriteUsersController}
          label={Translate.string('Editors')}
          eventId={eventId}
        />
      </Message>
    </FinalModalForm>
  );
}

TeamManager.propTypes = {
  editableType: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};
