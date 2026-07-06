// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {createPortal} from 'react-dom';
import {Button, Icon, SemanticICONS} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './ConfirmDialog.module.scss';

export interface TimetableConfirmDialogProps {
  message: React.ReactNode;
  title: string;
  type?: 'warning' | 'danger' | 'info';
  icon?: SemanticICONS;
  confirmLabel?: string;
  cancelLabel?: string;
  onClose: () => void;
  onConfirm: () => void;
}

export default function TimetableConfirmDialog({
  message,
  title,
  type = 'warning',
  icon = 'warning sign',
  confirmLabel = Translate.string('Proceed'),
  cancelLabel = Translate.string('Cancel'),
  onClose,
  onConfirm,
}: TimetableConfirmDialogProps) {
  // TODO: Create a context for dialog
  return createPortal(
    <div styleName="confirm-dialog-overlay" className="ui" onClick={onClose}>
      <div styleName={`confirm-dialog confirm-dialog-${type}`} onClick={e => e.stopPropagation()}>
        <button type="button" styleName="close-button" onClick={onClose}>
          <Icon name="close" size="large" />
        </button>

        <div styleName="dialog-content">
          <div styleName="dialog-title">
            <div styleName="dialog-icon">
              <Icon name={icon} />
            </div>
            {title}
          </div>
          <p styleName="dialog-message">{message}</p>

          <div styleName="dialog-actions">
            <Button basic size="small" onClick={onClose}>
              {cancelLabel}
            </Button>
            <Button primary size="small" onClick={onConfirm}>
              {confirmLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
