// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import Cropper from 'react-cropper';
import {Header, Icon, Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import 'cropperjs/dist/cropper.css';
import './Picture.module.scss';

export function PictureCropper({cropperRef, src, onCrop, backAction, minCropSize}) {
  const size = Math.max(minCropSize, 400) + 200;
  return (
    <div styleName="picture-outer-div">
      <div styleName="picture-inner-div cropper-inner-div" style={{width: size}}>
        <Header as="h3" color="grey">
          <Translate>Crop</Translate>
        </Header>
        <Cropper
          ref={cropperRef}
          style={{width: size, height: size}}
          zoomTo={0}
          initialAspectRatio={1}
          src={src}
          background={false}
          minCropBoxHeight={minCropSize}
          minCropBoxWidth={minCropSize}
          autoCropArea={1}
          checkOrientation={false}
          guides
          rotatable
        />
        <Icon
          styleName="back"
          name="arrow left"
          color="grey"
          size="large"
          onClick={() => backAction()}
        />
        <Button.Group>
          <Button
            styleName="cropper-action-btn"
            icon
            float="left"
            primary
            type="button"
            onClick={() => {
              if (cropperRef.current.cropper) {
                cropperRef.current.cropper.rotate(90);
              }
            }}
          >
            <Translate>Rotate</Translate>
            <Icon name="sync" />
          </Button>
          <Button
            type="button"
            float="left"
            styleName="cropper-action-btn"
            icon
            primary
            onClick={onCrop}
          >
            <Translate>Done</Translate>
            <Icon name="check" />
          </Button>
        </Button.Group>
      </div>
    </div>
  );
}

PictureCropper.propTypes = {
  cropperRef: PropTypes.object.isRequired,
  src: PropTypes.string.isRequired,
  onCrop: PropTypes.func.isRequired,
  backAction: PropTypes.func.isRequired,
  minCropSize: PropTypes.number,
};

PictureCropper.defaultProps = {
  minCropSize: 250,
};
