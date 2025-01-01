// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Dropdown, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {hasPublishableFiles} from '../selectors';

import './JudgmentDropdownItems.module.scss';

export default function JudgmentDropdownItems({options, judgmentType, setJudgmentType}) {
  const hasPublishables = useSelector(hasPublishableFiles);

  return options.map(({value, text, color}) => (
    <Popup
      content={Translate.string(
        'You cannot accept an editable that does not contain any publishable files.'
      )}
      trigger={
        <Dropdown.Item
          text={text}
          label={{color, empty: true, circular: true}}
          key={value}
          selected={value === judgmentType}
          styleName={!hasPublishables && value === 'accept' && 'disabled-item'}
          onClick={evt => {
            if (hasPublishables || value !== 'accept') {
              setJudgmentType(value);
            } else {
              evt.stopPropagation();
            }
          }}
        />
      }
      position="right center"
      key={value}
      disabled={hasPublishables || value !== 'accept'}
    />
  ));
}

JudgmentDropdownItems.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
      text: PropTypes.any,
      color: PropTypes.string,
      class: PropTypes.string,
    })
  ).isRequired,
  judgmentType: PropTypes.string,
  setJudgmentType: PropTypes.func.isRequired,
};

JudgmentDropdownItems.defaultProps = {
  judgmentType: null,
};
