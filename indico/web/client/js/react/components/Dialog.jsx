// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {forwardRef} from 'react';

const Dialog = forwardRef(function Dialog({children, ...props}, ref) {
  function handleBackdropClick(ev) {
    if (ev.target === ev.currentTarget) {
      ev.currentTarget.close();
    }
  }

  return (
    <dialog ref={ref} {...props} onClick={handleBackdropClick}>
      <div>{children}</div>
    </dialog>
  );
});

Dialog.propTypes = {
  children: PropTypes.oneOfType([PropTypes.node, PropTypes.arrayOf(PropTypes.node)]),
};

export default Dialog;
