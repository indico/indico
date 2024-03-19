// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Label, Segment} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {entryColorSchema, entrySchema} from '../util';

import './DetailsSegment.module.scss';

const actionShape = {
  icon: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  onClick: PropTypes.func,
  wrapper: PropTypes.elementType,
};

function ActionIcon({icon, onClick, title, color}) {
  return (
    <Icon
      name={icon}
      onClick={onClick}
      style={{color: color?.text || 'rgba(0, 0, 0, 0.6)'}}
      title={title}
      link
    />
  );
}

ActionIcon.propTypes = {
  ...actionShape,
  color: entryColorSchema,
};

ActionIcon.defaultProps = {
  color: null,
};

export default function DetailsSegment({
  title,
  subtitle,
  color,
  icon,
  actions,
  children,
  entry,
  dispatch,
  ...rest
}) {
  return (
    <Segment style={{borderColor: color?.background}} {...rest}>
      <Label
        style={{backgroundColor: color?.background, color: color?.text}}
        styleName="segment-header"
        attached="top"
      >
        {icon && <Icon name={icon} />}
        <Translate>{title}</Translate>
        {subtitle && <Label.Detail>{subtitle}</Label.Detail>}
        <div styleName="actions">
          {actions.map(({wrapper: Wrapper, ...action}) =>
            Wrapper ? (
              <Wrapper
                key={action.icon}
                trigger={<ActionIcon {...action} color={color} />}
                entry={entry}
                dispatch={dispatch}
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

DetailsSegment.propTypes = {
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.string,
  color: entryColorSchema,
  icon: PropTypes.string,
  actions: PropTypes.arrayOf(PropTypes.shape(actionShape)),
  children: PropTypes.node.isRequired,
  entry: entrySchema,
  dispatch: PropTypes.func,
};

DetailsSegment.defaultProps = {
  subtitle: '',
  icon: null,
  actions: [],
  color: {},
  entry: null,
  dispatch: () => {},
};
