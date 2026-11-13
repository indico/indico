// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';
import {Icon, Modal} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './SidebarDialog.module.scss';

/** Native focus boundary for the sidebar's informational dialogs. */
export default function SidebarDialog({open, onClose, title, short, children}) {
  const dialogRef = useRef(null);
  const closeRef = useRef(null);
  const headingRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!open) {
      return undefined;
    }
    const priorFocus = document.activeElement;
    dialog.showModal();
    (short ? closeRef : headingRef).current.focus();
    return () => {
      dialog.close();
      if (priorFocus?.isConnected) {
        priorFocus.focus();
      }
    };
  }, [open, short]);

  return (
    <dialog
      ref={dialogRef}
      className={`ui ${short ? 'tiny' : ''} modal`}
      styleName="dialog"
      aria-label={title}
      onClick={event => {
        if (event.target !== event.currentTarget) {
          return;
        }
        const bounds = event.currentTarget.getBoundingClientRect();
        if (
          event.clientX < bounds.left ||
          event.clientX > bounds.right ||
          event.clientY < bounds.top ||
          event.clientY > bounds.bottom
        ) {
          onClose();
        }
      }}
      onCancel={event => {
        event.preventDefault();
        onClose();
      }}
      onKeyDown={event => {
        if (event.key === 'Escape') {
          event.stopPropagation();
          return;
        }
        if (event.key !== 'Tab') {
          return;
        }
        const controls = [
          ...dialogRef.current.querySelectorAll('button, a[href], input, select, textarea'),
        ].filter(element => !element.disabled && element.getClientRects().length);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (
          event.shiftKey &&
          (document.activeElement === first || document.activeElement.tabIndex < 0)
        ) {
          event.preventDefault();
          last.focus();
        } else if (
          !event.shiftKey &&
          (document.activeElement === last || document.activeElement.tabIndex < 0)
        ) {
          event.preventDefault();
          first.focus();
        }
      }}
    >
      <button type="button" ref={closeRef} styleName="close" onClick={onClose}>
        <Icon name="close" />
        <span styleName="visually-hidden">
          <Translate>Close</Translate>
        </span>
      </button>
      <Modal.Header>
        <h2 ref={headingRef} tabIndex={-1}>
          {title}
        </h2>
      </Modal.Header>
      <Modal.Content>{children}</Modal.Content>
    </dialog>
  );
}

SidebarDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  short: PropTypes.bool,
  children: PropTypes.node.isRequired,
};

SidebarDialog.defaultProps = {
  short: false,
};
