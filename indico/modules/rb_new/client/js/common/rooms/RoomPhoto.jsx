/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import roomPhotoURL from 'indico-url:rooms_new.admin_room_photo';

import React, {useCallback, useState, useEffect, useRef} from 'react';
import PropTypes from 'prop-types';
import Dropzone from 'react-dropzone';
import {Button, Dimmer, Icon, Image, Popup, Loader} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';

import './RoomPhoto.module.scss';


export default function RoomPhoto({roomId, hasPhoto}) {
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
        setFile(null);
        setLoading(false);
        setHasPreview(false);
    };

    const savePhoto = async () => {
        setLoading(true);
        try {
            const bodyFormData = new FormData();
            bodyFormData.append('photo', file);
            const config = {
                headers: {'content-type': 'multipart/form-data'}
            };
            await indicoAxios.post(roomPhotoURL({room_id: roomId}), bodyFormData, config);
        } catch (e) {
            handleAxiosError(e);
        }
        setFile(null);
        setLoading(false);
        setHasPreview(true);
    };

    const cancelPhoto = () => {
        setFile(null);
        setHasPreview(hasPhoto);
    };

    const getPreview = () => {
        const randomId = new Date().getTime();
        return file ? URL.createObjectURL(file) : `${roomPhotoURL({room_id: roomId})}?random=${randomId}`;
    };

    const dropzoneRef = useRef();

    const openDialog = () => {
        // Note that the ref is set async, so it might be null at some point
        if (dropzoneRef.current) {
            dropzoneRef.current.open();
        }
    };

    const uploadBtn = (
        <Button disabled={loading} type="button" styleName="upload-icon" size="small" onClick={openDialog}>
            <Icon name="upload" /><Translate>Upload</Translate>
        </Button>
    );

    const saveBtn = (
        <Button disabled={loading || !file}
                type="button"
                styleName="save-icon"
                size="small"
                onClick={savePhoto}>
            <Icon name="check" /><Translate>Save</Translate>
        </Button>
    );

    const deleteBtn = (
        <Button disabled={!hasPreview || loading}
                type="button"
                styleName="remove-icon"
                size="small"
                onClick={deletePhoto}>
            <Icon name="trash" /><Translate>Delete</Translate>
        </Button>
    );

    const cancelBtn = (
        <Button disabled={loading}
                type="button"
                size="small"
                onClick={cancelPhoto}>
            <Icon name="dont" /><Translate>Cancel</Translate>
        </Button>
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
            {hasPreview && (
                <Dimmer.Dimmable>
                    <Dimmer active={loading}>
                        <Loader />
                    </Dimmer>
                    <Image className="img" src={getPreview()} />
                </Dimmer.Dimmable>
            )}
            {!hasPreview && <Translate>No photo found.</Translate>}
        </div>
    );

    return (
        <Dropzone ref={dropzoneRef}
                  onDrop={onDrop}
                  multiple={false}
                  noClick
                  noKeyboard
                  noDrag>
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
    hasPhoto: PropTypes.bool
};

RoomPhoto.defaultProps = {
    hasPhoto: false,
};
