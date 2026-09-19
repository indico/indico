// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import 'indico/custom_elements/ind_with_popup';

/**
 * React wrapper around the `ind-with-popup` custom element.
 *
 * `trigger` must contain an element carrying the `data-trigger` attribute (the
 * button that opens the popup). `children` are rendered inside the popup's
 * `<dialog>`; the wrapping element receives focus when the popup opens.
 */
export default function WithPopup({trigger, children}) {
  return (
    <ind-with-popup>
      {trigger}
      <dialog data-dialog>
        <div tabIndex={-1}>{children}</div>
      </dialog>
    </ind-with-popup>
  );
}

WithPopup.propTypes = {
  trigger: PropTypes.node.isRequired,
  children: PropTypes.node.isRequired,
};
