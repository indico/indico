// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './PlaceholderInfo.module.scss';

const placeholderShape = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool,
  description: PropTypes.node,
  advanced: PropTypes.bool,
  parametrized: PropTypes.bool,
  params: PropTypes.arrayOf(
    PropTypes.shape({
      param: PropTypes.string,
      description: PropTypes.node.isRequired,
    })
  ),
};

function SinglePlaceholderInfo({name, description, required, jinja}) {
  return (
    <li>
      <code>{jinja ? `{{ ${name} }}` : `{${name}}`}</code>
      <span styleName="description"> – {description}</span>
      {required && (
        <span styleName="required">
          (<Translate>required</Translate>)
        </span>
      )}
    </li>
  );
}

SinglePlaceholderInfo.propTypes = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool,
  description: PropTypes.node.isRequired,
  jinja: PropTypes.bool.isRequired,
};

SinglePlaceholderInfo.defaultProps = {
  required: false,
};

function ParametrizedPlaceholderInfo({name, required, params, jinja}) {
  const paramName = param => (jinja ? `${name}.${param}` : `${name}:${param}`);
  return params.map(({param, description}) => (
    <SinglePlaceholderInfo
      key={param ? paramName(param) : name}
      name={param ? paramName(param) : name}
      required={required}
      description={description}
      jinja={jinja}
    />
  ));
}

ParametrizedPlaceholderInfo.propTypes = {
  ...placeholderShape,
  jinja: PropTypes.bool.isRequired,
};

function PlaceholderInfoBox({placeholders, jinja}) {
  return (
    <ul styleName="placeholder-info">
      {placeholders
        .filter(p => p.description)
        .map(placeholder => (
          <SinglePlaceholderInfo key={placeholder.name} {...placeholder} jinja={jinja} />
        ))}
      {placeholders
        .filter(p => p.parametrized)
        .map(placeholder => (
          <ParametrizedPlaceholderInfo key={placeholder.name} {...placeholder} jinja={jinja} />
        ))}
    </ul>
  );
}

PlaceholderInfoBox.propTypes = {
  placeholders: PropTypes.arrayOf(PropTypes.shape(placeholderShape)).isRequired,
  jinja: PropTypes.bool.isRequired,
};

export default function PlaceholderInfo({placeholders, defaultOpen, jinja}) {
  const simplePlaceholders = placeholders.filter(p => !p.advanced);
  const advancedPlaceholders = placeholders.filter(p => p.advanced);

  const panels = [
    {
      key: 'simple',
      title: Translate.string('Available placeholders'),
      content: {
        content: <PlaceholderInfoBox placeholders={simplePlaceholders} jinja={jinja} />,
      },
    },
  ];
  if (advancedPlaceholders.length > 0) {
    panels.push({
      key: 'advanced',
      title: Translate.string('Advanced placeholders'),
      content: {
        content: <PlaceholderInfoBox placeholders={advancedPlaceholders} jinja={jinja} />,
      },
    });
  }

  return (
    <Accordion
      defaultActiveIndex={defaultOpen ? [0] : []}
      panels={panels}
      exclusive={false}
      styled
      fluid
    />
  );
}

PlaceholderInfo.propTypes = {
  placeholders: PropTypes.arrayOf(PropTypes.shape(placeholderShape)).isRequired,
  defaultOpen: PropTypes.bool,
  jinja: PropTypes.bool,
};

PlaceholderInfo.defaultProps = {
  defaultOpen: false,
  jinja: false,
};
