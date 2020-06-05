// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {blockPropTypes} from '../util';
import {EditingReviewAction} from '../../../models';
import AcceptRejectForm from './AcceptRejectForm';
import RequestChangesForm from './RequestChangesForm';
import UpdateFilesForm from './UpdateFilesForm';
import JudgmentDropdownItems from './JudgmentDropdownItems';

import './JudgmentBox.module.scss';

export default function JudgmentBox({block, onClose, judgmentType: _judgmentType, options}) {
  const [judgmentType, setJudgmentType] = useState(_judgmentType);
  const [loading, setLoading] = useState(false);
  const option = options.find(x => x.value === judgmentType);

  return (
    <>
      <div styleName="choice-bar">
        <h3>
          <Translate>Your decision</Translate>
        </h3>
        <div>
          <Dropdown
            value={judgmentType}
            text={option.text}
            direction="left"
            disabled={loading}
            button
            floating
            styleName="judgment-type-button"
            className={option.class}
          >
            <Dropdown.Menu>
              <JudgmentDropdownItems
                options={options}
                judgmentType={judgmentType}
                setJudgmentType={setJudgmentType}
              />
            </Dropdown.Menu>
          </Dropdown>
          <Button icon="delete" disabled={loading} onClick={onClose} />
        </div>
      </div>
      {[EditingReviewAction.accept, EditingReviewAction.reject].includes(judgmentType) && (
        <AcceptRejectForm block={block} action={judgmentType} setLoading={setLoading} />
      )}
      {judgmentType === EditingReviewAction.update && <UpdateFilesForm setLoading={setLoading} />}
      {judgmentType === EditingReviewAction.requestUpdate && (
        <RequestChangesForm setLoading={setLoading} onSuccess={onClose} />
      )}
    </>
  );
}

JudgmentBox.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  judgmentType: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
      text: PropTypes.string,
      class: PropTypes.string,
    })
  ).isRequired,
  onClose: PropTypes.func,
};

JudgmentBox.defaultProps = {
  onClose: null,
};
