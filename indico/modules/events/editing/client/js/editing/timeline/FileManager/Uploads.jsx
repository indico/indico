// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Message, Popup, Progress} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './FileManager.module.scss';

export default function Uploads({uploads}) {
  const uploadList = _.sortBy(Object.entries(uploads), x => x[0]);
  return (
    <div styleName="uploading-file-list">
      {uploadList.map(
        ([
          key,
          {
            file: {name},
            percent,
            failed,
          },
        ]) => (
          <Popup
            key={key}
            on="hover"
            disabled={!failed}
            position="right center"
            content={Translate.string('An error occurred while uploading this file')}
            trigger={
              <Message styleName="uploading-file-row" negative={failed}>
                <Icon loading={!failed} name={failed ? 'exclamation' : 'spinner'} />
                <span styleName="file-state" className={failed ? 'error' : 'uploading'}>
                  {name}
                </span>
                {!failed && <Progress percent={percent} attached="bottom" color="blue" />}
              </Message>
            }
          />
        )
      )}
    </div>
  );
}

Uploads.propTypes = {
  uploads: PropTypes.objectOf(
    PropTypes.shape({
      file: PropTypes.shape({
        name: PropTypes.string.isRequired,
      }).isRequired,
      percent: PropTypes.number,
    })
  ).isRequired,
};
