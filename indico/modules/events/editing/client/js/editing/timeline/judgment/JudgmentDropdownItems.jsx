// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Dropdown, Popup} from 'semantic-ui-react';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {hasPublishableFiles} from '../selectors';

import './JudgmentDropdownItems.module.scss';

export default function JudgmentDropdownItems({options, judgmentType, setJudgmentType}) {
  const hasPublishables = useSelector(hasPublishableFiles);

  return options.map(({value, text}) => (
    <Popup
      content={Translate.string(
        'You cannot accept an editable that does not contain any publishable files.'
      )}
      trigger={
        <Dropdown.Item
          text={text}
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
      text: PropTypes.string,
      class: PropTypes.string,
    })
  ).isRequired,
  judgmentType: PropTypes.string,
  setJudgmentType: PropTypes.func.isRequired,
};

JudgmentDropdownItems.defaultProps = {
  judgmentType: null,
};
