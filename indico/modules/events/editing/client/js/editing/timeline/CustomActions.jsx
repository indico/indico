// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {useDispatch} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Confirm, Divider} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {loadTimeline} from './actions';

import './CustomActions.module.scss';

export default function CustomActions({url, actions}) {
  const [confirmAction, setConfirmAction] = useState(null);
  const [submitting, setSubmitting] = useState(null);
  const dispatch = useDispatch();

  const triggerAction = async name => {
    setConfirmAction(null);
    setSubmitting(name);
    let resp;
    try {
      resp = await indicoAxios.post(url, {action: name});
    } catch (err) {
      setSubmitting(null);
      handleAxiosError(err);
      return;
    }

    if (resp.data.redirect) {
      location.href = resp.data.redirect;
      return;
    }

    await dispatch(loadTimeline());
    setSubmitting(null);
  };

  const handleActionClick = action => {
    if (action.confirm) {
      setConfirmAction(action);
    } else {
      triggerAction(action.name);
    }
  };

  return (
    <>
      <Divider horizontal styleName="divider">
        <Translate>Actions</Translate>
      </Divider>
      <Button.Group floated="right">
        {actions.map(a => (
          <Button
            key={a.name}
            content={a.title}
            color={a.color}
            icon={a.icon}
            onClick={() => handleActionClick(a)}
            disabled={!!submitting}
            loading={submitting === a.name}
          />
        ))}
      </Button.Group>
      {confirmAction && (
        <Confirm
          size="mini"
          onCancel={() => setConfirmAction(null)}
          onConfirm={() => triggerAction(confirmAction.name)}
          header={Translate.string('Confirm action: {action}', {action: confirmAction.title})}
          content={confirmAction.confirm}
          confirmButton={Translate.string('OK')}
          cancelButton={Translate.string('Cancel')}
          open
        />
      )}
    </>
  );
}

CustomActions.propTypes = {
  url: PropTypes.string.isRequired,
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      color: PropTypes.string,
      icon: PropTypes.string,
      confirm: PropTypes.string,
    })
  ).isRequired,
};
