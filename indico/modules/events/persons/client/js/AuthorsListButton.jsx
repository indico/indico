// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {Translate} from 'indico/react/i18n';

import {AuthorsList, CONTEXTS} from './AuthorsList';
import {getIds} from './util';

export function AuthorsListButton({eventId, objectContext, paramsSelector}) {
  const [open, setOpen] = useState(false);
  const sourceIds = getIds(paramsSelector);

  return (
    <>
      <button
        type="button"
        className="i-button icon-users js-requires-selected-row disabled"
        onClick={evt => {
          if (!evt.target.classList.contains('disabled')) {
            setOpen(true);
          }
        }}
      >
        <Translate>Authors list</Translate>
      </button>
      {open && (
        <AuthorsList
          eventId={eventId}
          sourceIds={sourceIds}
          objectContext={objectContext}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

AuthorsListButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  objectContext: PropTypes.oneOf(Object.keys(CONTEXTS)).isRequired,
  paramsSelector: PropTypes.string.isRequired,
};
