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

import './ActionPrompt.module.scss';

export interface TimetableActionPromptProps {
  message: React.ReactNode;
  type?: 'warning' | 'danger' | 'info';
  icon?: SemanticICONS;
  confirmLabel?: string;
  cancelLabel?: string;
  onClose: () => void;
  onConfirm: () => void;
}

export default function TimetableActionPrompt({
  message,
  type = 'warning',
  icon = 'warning sign',
  confirmLabel = Translate.string('Proceed'),
  cancelLabel = Translate.string('Cancel'),
  onClose,
  onConfirm,
}: TimetableActionPromptProps) {
  return createPortal(
    <div styleName="action-prompt-overlay">
      <div styleName={`action-prompt action-prompt-${type}`}>
        <button type="button" styleName="close-button" onClick={onClose}>
          <Icon name="close" />
        </button>

        <div styleName="prompt-icon">
          <Icon name={icon} />
        </div>

        <div styleName="prompt-content">
          <div styleName="prompt-message">{message}</div>

          <div styleName="prompt-actions">
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
