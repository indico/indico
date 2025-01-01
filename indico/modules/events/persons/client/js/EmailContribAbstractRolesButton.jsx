// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
  className,
}) {
  const [open, setOpen] = useState(false);
  const ids = idSelector && getIds(idSelector);
  const idType = {abstracts: 'abstract_id', contributions: 'contribution_id'}[objectContext];

  return (
    <>
      <button
        type="button"
        className={`i-button icon-mail ${className}`}
        onClick={evt => {
          if (!evt.target.classList.contains('disabled')) {
            setOpen(true);
          }
        }}
      >
        <Translate>Send email</Translate>
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
  idSelector: PropTypes.string,
  metadataURL: PropTypes.string.isRequired,
  previewURL: PropTypes.string.isRequired,
  sendURL: PropTypes.string.isRequired,
  className: PropTypes.string,
};

EmailContribAbstractRolesButton.defaultProps = {
  idSelector: null,
  className: '',
};
