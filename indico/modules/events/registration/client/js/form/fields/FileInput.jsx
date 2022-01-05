// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';
import {Button, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function FileInput({htmlName}) {
  const [file, setFile] = useState();
  const fileRef = useRef();

  const handleFileChange = e => {
    setFile(e.target.value.split('\\').pop());
  };

  const handleFileClear = () => {
    setFile(null);
    fileRef.current.value = null;
  };

  const handleSelectFileClick = () => {
    fileRef.current.click();
  };

  return (
    <>
      <Button.Group size="small">
        <Button
          type="button"
          htmlFor={`${htmlName}-file`}
          name={htmlName}
          icon="upload"
          label={
            <Label styleName={file ? 'fileinput-label-squarecorners' : ''}>
              <span styleName="fileinput-label">
                {file ? file : <Translate>Select File</Translate>}
              </span>
            </Label>
          }
          onClick={handleSelectFileClick}
        />
        {file && <Button icon="delete" onClick={handleFileClear} />}
      </Button.Group>
      <input id={`${htmlName}-file`} hidden type="file" ref={fileRef} onChange={handleFileChange} />
    </>
  );
}

FileInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
};
