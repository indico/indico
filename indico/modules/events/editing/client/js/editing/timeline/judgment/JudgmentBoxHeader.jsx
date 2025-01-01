// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Button, Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import JudgmentDropdownItems from './JudgmentDropdownItems';

import './JudgmentBoxHeader.module.scss';

export default function JudgmentBoxHeader({judgmentType, setJudgmentType, options, loading}) {
  const option = options.find(x => x.value === judgmentType);

  return (
    <div styleName="choice-bar">
      <h3>
        <Translate>Your decision</Translate>
      </h3>
      <div>
        <Dropdown
          value={judgmentType}
          trigger={
            <Dropdown.Text className="text">
              <div
                className={`ui empty circular ${option.color} label`}
                style={{marginRight: '0.5em', verticalAlign: '-10%'}}
              />
              {option.text}
            </Dropdown.Text>
          }
          direction="left"
          disabled={loading}
          button
          floating
        >
          <Dropdown.Menu>
            <JudgmentDropdownItems
              options={options}
              judgmentType={judgmentType}
              setJudgmentType={setJudgmentType}
            />
          </Dropdown.Menu>
        </Dropdown>
        <Button icon="delete" disabled={loading} onClick={() => setJudgmentType(null)} />
      </div>
    </div>
  );
}

JudgmentBoxHeader.propTypes = {
  judgmentType: PropTypes.string.isRequired,
  setJudgmentType: PropTypes.func.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
      text: PropTypes.string,
      class: PropTypes.string,
      color: PropTypes.string,
    })
  ).isRequired,
  loading: PropTypes.bool.isRequired,
};
