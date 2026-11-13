// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

export default function CategoryActionElement({
  category,
  actionButtonText,
  isNavigation,
  actionUrl,
  disabled,
  disabledMessage,
  onAction,
}) {
  const isLink = Boolean(isNavigation && actionUrl && !disabled);
  const labelContent = (
    <>
      {actionButtonText}
      {category?.title && (
        // A plain space next to the out-of-flow hidden text is collapsed away and the words run together
        <span className="visually-hidden">{`\u00a0${category.title}`}</span>
      )}
    </>
  );

  if (disabled) {
    const disabledButton = (
      <button type="button" className="category-action-button disabled" disabled>
        {labelContent}
        {disabledMessage && <span data-tip-content>{disabledMessage}</span>}
      </button>
    );

    if (disabledMessage) {
      return <ind-with-tooltip>{disabledButton}</ind-with-tooltip>;
    }
    return disabledButton;
  }

  if (isLink) {
    const href = typeof actionUrl === 'function' ? actionUrl(category) : actionUrl;
    return (
      <a
        href={href}
        className="category-action-button"
        onClick={evt => {
          // Browsers other than on macOS ignore Meta on links; navigate here as the old widget did
          if (
            evt.metaKey &&
            !evt.ctrlKey &&
            !evt.shiftKey &&
            !/Mac|iPhone|iPad/.test(navigator.platform)
          ) {
            evt.preventDefault();
            window.location.assign(href);
          }
        }}
      >
        {labelContent}
      </a>
    );
  }

  return (
    <button
      type="button"
      className="category-action-button"
      onClick={() => {
        if (onAction) {
          onAction(category);
        }
      }}
    >
      {labelContent}
    </button>
  );
}

CategoryActionElement.propTypes = {
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
  }).isRequired,
  actionButtonText: PropTypes.string.isRequired,
  isNavigation: PropTypes.bool,
  actionUrl: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  disabled: PropTypes.bool,
  disabledMessage: PropTypes.string,
  onAction: PropTypes.func,
};

CategoryActionElement.defaultProps = {
  isNavigation: false,
  actionUrl: null,
  disabled: false,
  disabledMessage: '',
  onAction: null,
};
