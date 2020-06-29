// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:event_editing.api_editable_type_principals';

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Loader, Message, Modal} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {FinalPrincipalList} from 'indico/react/components';
import {
  getChangedValues,
  handleSubmitError,
  FinalSubmitButton,
  FinalUnloadPrompt,
} from 'indico/react/forms';
import {indicoAxios} from 'indico/utils/axios';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {useNumericParam} from 'indico/react/util/routing';

export default function TeamManager({editableType, onClose}) {
  const eventId = useNumericParam('confId');
  const favoriteUsersController = useFavoriteUsers();

  const {data: principals, loading: isLoadingPrincipals} = useIndicoAxios({
    url: principalsURL({confId: eventId, type: editableType}),
    trigger: [eventId, editableType],
  });

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    try {
      await indicoAxios.post(principalsURL({confId: eventId, type: editableType}), changedValues);
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
    <div style={{padding: '30'}}>
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={{principals}}
        initialValuesEqual={_.isEqual}
        subscription={{}}
      >
        {fprops => (
          <Modal onClose={onClose} size="small" closeOnDimmerClick={false} open>
            <Modal.Header content={Translate.string('Set editors')} />
            <Modal.Content>
              <Form id="team-manager-form" onSubmit={fprops.handleSubmit}>
                <FinalUnloadPrompt />
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
              </Form>
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              <FinalSubmitButton form="team-manager-form" label={Translate.string('Submit')} />
              <Button onClick={onClose} disabled={fprops.submitting}>
                <Translate>Cancel</Translate>
              </Button>
            </Modal.Actions>
          </Modal>
        )}
      </FinalForm>
    </div>
  );
}

TeamManager.propTypes = {
  editableType: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};
