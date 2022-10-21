// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './PlaceholderInfo.module.scss';

const placeholderShape = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool.isRequired,
  description: PropTypes.string,
  advanced: PropTypes.bool.isRequired,
  parametrized: PropTypes.bool.isRequired,
  params: PropTypes.arrayOf(
    PropTypes.shape({
      param: PropTypes.string,
      description: PropTypes.string.isRequired,
    })
  ),
};

function SinglePlaceholderInfo({name, description, required}) {
  return (
    <li>
      <code>{`{${name}}`}</code> - {description}
      {required && (
        <span styleName="required">
          {'('}
          <Translate>required</Translate>
          {')'}
        </span>
      )}
    </li>
  );
}

SinglePlaceholderInfo.propTypes = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool.isRequired,
  description: PropTypes.string.isRequired,
};

function ParametrizedPlaceholderInfo({name, required, params}) {
  return params.map(({param, description}) => (
    <SinglePlaceholderInfo
      key={param ? `${name}:${param}` : name}
      name={param ? `${name}:${param}` : name}
      required={required}
      description={description}
    />
  ));
}

ParametrizedPlaceholderInfo.propTypes = placeholderShape;

function PlaceholderInfoBox({placeholders}) {
  return (
    <ul>
      {placeholders
        .filter(p => p.description)
        .map(placeholder => (
          <SinglePlaceholderInfo key={placeholder.name} {...placeholder} />
        ))}
      {placeholders
        .filter(p => p.parametrized)
        .map(placeholder => (
          <ParametrizedPlaceholderInfo key={placeholder.name} {...placeholder} />
        ))}
    </ul>
  );
}

PlaceholderInfoBox.propTypes = {
  placeholders: PropTypes.arrayOf(PropTypes.shape(placeholderShape)).isRequired,
};

export default function PlaceholderInfo({placeholders}) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const simplePlaceholders = placeholders.filter(p => !p.advanced);
  const advancedPlaceholders = placeholders.filter(p => p.advanced);

  return (
    <div styleName="placeholderInfo">
      <Form.Field>
        <Translate as="label">Available placeholders</Translate>
        <PlaceholderInfoBox placeholders={simplePlaceholders} />
      </Form.Field>
      {advancedPlaceholders.length > 0 && (
        <Form.Field>
          <Translate as="label" styleName="advancedHeader">
            Advanced placeholders
          </Translate>
          <span styleName="advancedToggle">
            {'('}
            <a onClick={() => setShowAdvanced(!showAdvanced)}>
              {showAdvanced ? Translate.string('hide') : Translate.string('show')}
            </a>
            {')'}
          </span>
          {showAdvanced && <PlaceholderInfoBox placeholders={advancedPlaceholders} />}
        </Form.Field>
      )}
    </div>
  );
}

PlaceholderInfo.propTypes = {
  placeholders: PropTypes.arrayOf(PropTypes.shape(placeholderShape)).isRequired,
};
