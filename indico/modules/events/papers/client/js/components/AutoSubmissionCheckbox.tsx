// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import autoSubmissionURL from 'indico-url:papers.manage_submission_settings';

import React from 'react';
import {Icon, Popup, Message} from 'semantic-ui-react';

import {Checkbox} from 'indico/react/components';
import {useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import './AutoSubmissionCheckbox.module.scss';

interface AutoSumbissionCheckboxProps {
  eventId: number;
}

export default function AutoSubmissionCheckbox({eventId}: AutoSumbissionCheckboxProps) {
  const [autoSubmissionEnabled, toggleAutoSubmission, autoSubmissionLoading, autoSubmissionSaving] =
    useTogglableValue(autoSubmissionURL({event_id: eventId}));

  return (
    <div styleName="informative-checkbox">
      <Checkbox
        styleName="toolbar-checkbox toolbar-checkbox--no-padding"
        showAsToggle
        checked={autoSubmissionEnabled}
        onChange={!autoSubmissionSaving ? toggleAutoSubmission : null}
        label={Translate.string('Enable auto submission from peer-review')}
        disabled={autoSubmissionLoading}
        indeterminate={false}
        className=""
        style={{}}
      />
      <Popup
        size="mini"
        trigger={<Icon styleName="informative-icon" name="info circle" />}
        content={
          <Message info icon>
            <Icon name="warning sign" />
            <Message.Content>
              <Message.Header>
                <Translate>Auto submission from peer-review</Translate>
              </Message.Header>
              <Translate>
                When enabled, file types from the Editing module are synchronized to the Peer Review
                module. Synchronized file types cannot be modified in Peer Review; they can only be
                managed in Editing.
              </Translate>
            </Message.Content>
          </Message>
        }
      />
    </div>
  );
}
