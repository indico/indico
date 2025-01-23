// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Icon, Label, Segment, SemanticICONS} from 'semantic-ui-react';

import {toClasses} from 'indico/react/util';

import {Entry} from '../types';

import './DetailsSegment.module.scss';

interface Action {
  icon: SemanticICONS;
  title: string;
  onClick: (e: React.MouseEvent) => void;
  wrapper?: React.ComponentType<{trigger: React.ReactElement; entry: Entry}>;
}

interface ActionIconProps extends Action {
  color?: {text: string; background: string};
}

function ActionIcon({icon, onClick, title, color}: ActionIconProps) {
  return (
    <Icon
      name={icon}
      onClick={e => {
        e.stopPropagation();
        onClick(e);
      }}
      style={{color: color?.text || 'rgba(0, 0, 0, 0.6)'}}
      title={title}
      link
    />
  );
}

export default function DetailsSegment({
  title,
  subtitle,
  color,
  icon,
  actions,
  children,
  entry,
  selected,
  ...rest
}: {
  title: string;
  subtitle?: string;
  color?: {text: string; background: string};
  icon?: SemanticICONS;
  actions: Action[];
  children: React.ReactNode;
  entry: Entry;
  selected?: boolean;
}) {
  return (
    <Segment style={{borderColor: color?.background}} {...rest}>
      <Label
        style={{backgroundColor: color?.background, color: color?.text}}
        styleName={toClasses({'segment-header': true, selected})}
        attached="top"
      >
        {icon && <Icon name={icon} />}
        {title}
        {subtitle && <Label.Detail>{subtitle}</Label.Detail>}
        <div styleName="actions">
          {actions.map(({wrapper: Wrapper, ...action}) =>
            Wrapper ? (
              <Wrapper
                key={action.icon}
                trigger={<ActionIcon {...action} color={color} />}
                entry={entry}
              />
            ) : (
              <ActionIcon key={action.icon} {...action} color={color} />
            )
          )}
        </div>
      </Label>
      {children}
    </Segment>
  );
}
