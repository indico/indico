// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import roomPhotoURL from 'indico-url:rb.admin_room_photo';

import React, {useCallback, useState, useEffect, useRef} from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone';
import {Button, Dimmer, Image, Popup, Loader} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';
import {actions as configActions} from '../../config';

import './RoomPhoto.module.scss';

function RoomPhoto({roomId, hasPhoto, setRoomsSpriteToken}) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasPreview, setHasPreview] = useState(false);

  useEffect(() => {
    setHasPreview(hasPhoto);
  }, [hasPhoto]);

  const onDrop = useCallback(acceptedFiles => {
    setFile(acceptedFiles[0]);
    setHasPreview(true);
  }, []);

  const deletePhoto = async () => {
    setLoading(true);
    try {
      await indicoAxios.delete(roomPhotoURL({room_id: roomId}));
    } catch (e) {
      handleAxiosError(e);
    }
    setHasPreview(false);
    setFile(null);
    setLoading(false);
  };

  const savePhoto = async () => {
    setLoading(true);
    const bodyFormData = new FormData();
    bodyFormData.append('photo', file);
    const config = {
      headers: {'content-type': 'multipart/form-data'},
    };
    let response;
    try {
      response = await indicoAxios.post(roomPhotoURL({room_id: roomId}), bodyFormData, config);
    } catch (e) {
      handleAxiosError(e);
      setLoading(false);
      return;
    }
    setFile(null);
    setLoading(false);
    setHasPreview(true);
    setRoomsSpriteToken(response.data.rooms_sprite_token);
  };

  const cancelPhoto = () => {
    setFile(null);
    setHasPreview(hasPhoto);
  };

  const getPreview = () => {
    return file ? URL.createObjectURL(file) : `${roomPhotoURL({room_id: roomId})}?_=${+Date.now()}`;
  };

  const dropzoneRef = useRef();

  const openDialog = () => {
    // Note that the ref is set async, so it might be null at some point
    if (dropzoneRef.current) {
      dropzoneRef.current.open();
    }
  };

  const uploadBtn = (
    <Button
      disabled={loading}
      type="button"
      icon="upload"
      content={Translate.string('Upload')}
      styleName="upload-icon"
      size="small"
      onClick={openDialog}
    />
  );

  const saveBtn = (
    <Button
      disabled={loading || !file}
      loading={loading}
      type="button"
      icon="check"
      content={Translate.string('Save')}
      styleName="save-icon"
      size="small"
      onClick={savePhoto}
    />
  );

  const deleteBtn = (
    <Button
      disabled={!hasPreview || loading}
      loading={loading}
      type="button"
      icon="trash"
      content={Translate.string('Delete')}
      styleName="remove-icon"
      size="small"
      onClick={deletePhoto}
    />
  );

  const cancelBtn = (
    <Button
      disabled={loading}
      type="button"
      icon="dont"
      content={Translate.string('Cancel')}
      size="small"
      onClick={cancelPhoto}
    />
  );

  const buttons = (
    <div styleName="photo-actions">
      {file ? (
        <>
          <Popup trigger={saveBtn} content={Translate.string('Save photo')} />
          <Popup trigger={cancelBtn} content={Translate.string('Cancel photo upload')} />
        </>
      ) : (
        <>
          <Popup trigger={uploadBtn} content={Translate.string('Upload a new photo')} />
          <Popup trigger={deleteBtn} content={Translate.string('Delete existing photo')} />
        </>
      )}
    </div>
  );

  const thumbnail = (
    <div>
      {hasPreview ? (
        <Dimmer.Dimmable>
          <Dimmer active={loading}>
            <Loader />
          </Dimmer>
          <Image className="img" src={getPreview()} />
        </Dimmer.Dimmable>
      ) : (
        <Translate>No photo found.</Translate>
      )}
    </div>
  );

  return (
    <Dropzone
      ref={dropzoneRef}
      onDrop={onDrop}
      multiple={false}
      noClick
      noKeyboard
      accept="image/*"
    >
      {({getRootProps, getInputProps}) => (
        <section>
          <div {...getRootProps()} styleName="dropzone">
            <input {...getInputProps()} />
            {thumbnail}
            {buttons}
          </div>
        </section>
      )}
    </Dropzone>
  );
}

RoomPhoto.propTypes = {
  roomId: PropTypes.number.isRequired,
  hasPhoto: PropTypes.bool,
  setRoomsSpriteToken: PropTypes.func.isRequired,
};

RoomPhoto.defaultProps = {
  hasPhoto: false,
};

export default connect(
  null,
  {setRoomsSpriteToken: configActions.setRoomsSpriteToken}
)(RoomPhoto);
