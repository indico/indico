// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import Webcam from 'react-webcam';
import {Header, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import './Picture.module.scss';

export function PictureWebcam({
  cameraRef,
  height,
  width,
  onCapture,
  onUserMediaError,
  backAction,
  minSize,
}) {
  const [userMediaActive, setUserMediaActive] = useState(false);
  height = Math.max(height, minSize) + 100;
  width = Math.max(height, minSize) + 100;
  return (
    <>
      {!userMediaActive && (
        <Icon styleName="loading-overlay" loading name="spinner" size="huge" color="grey" />
      )}
      <div
        styleName={userMediaActive ? 'picture-outer-div show' : 'picture-outer-div hidden'}
        onClick={onCapture}
      >
        <div id="picture-inner-div" styleName="picture-inner-div">
          <Header as="h3" icon textAlign="center" color="grey">
            <Translate>Camera</Translate>
          </Header>
          <Webcam
            ref={cameraRef}
            audio={false}
            height={height}
            width={width}
            screenshotFormat="image/png"
            onUserMediaError={onUserMediaError}
            onUserMedia={() => setUserMediaActive(true)}
            mirrored
          />
          <p>
            <Translate>Click anywhere on the image to take a picture</Translate>
          </p>
          <Icon
            styleName="back"
            name="arrow left"
            color="grey"
            size="large"
            onClick={evt => {
              evt.stopPropagation(); // avoid opening the cropper
              backAction();
            }}
          />
        </div>
      </div>
    </>
  );
}

PictureWebcam.propTypes = {
  cameraRef: PropTypes.object.isRequired,
  height: PropTypes.number,
  width: PropTypes.number,
  minSize: PropTypes.number,
  onCapture: PropTypes.func.isRequired,
  onUserMediaError: PropTypes.func,
  backAction: PropTypes.func.isRequired,
};

PictureWebcam.defaultProps = {
  height: 400,
  width: 400,
  minSize: 250,
  onUserMediaError: null,
};
