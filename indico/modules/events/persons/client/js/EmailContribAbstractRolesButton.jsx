// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {Translate} from 'indico/react/i18n';

import {EmailContribAbstractRoles} from './EmailContribAbstractRoles';
import {getIds} from './util';

export function EmailContribAbstractRolesButton({
  objectContext,
  idSelector,
  metadataURL,
  previewURL,
  sendURL,
}) {
  const [open, setOpen] = useState(false);
  const ids = getIds(idSelector);
  const idType = {abstracts: 'abstract_id', contributions: 'contribution_id'}[objectContext];

  return (
    <>
      <button
        type="button"
        className="i-button icon-mail js-requires-selected-row disabled"
        onClick={evt => {
          if (!evt.target.classList.contains('disabled')) {
            setOpen(true);
          }
        }}
      >
        <Translate>Email</Translate>
      </button>
      {open && (
        <EmailContribAbstractRoles
          context={{[idType]: ids}}
          metadataURL={metadataURL}
          previewURL={previewURL}
          sendURL={sendURL}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

EmailContribAbstractRolesButton.propTypes = {
  objectContext: PropTypes.oneOf(['abstracts', 'contributions']).isRequired,
  idSelector: PropTypes.string.isRequired,
  metadataURL: PropTypes.string.isRequired,
  previewURL: PropTypes.string.isRequired,
  sendURL: PropTypes.string.isRequired,
};
