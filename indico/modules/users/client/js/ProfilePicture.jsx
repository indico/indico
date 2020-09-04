// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageURL from 'indico-url:users.manage_profile_picture';
import pictureURL from 'indico-url:users.profile_picture_display';
import gravatarURL from 'indico-url:users.profile_picture_gravatar';

import React, {useState, useCallback} from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import {Form as FinalForm, useField, useFormState} from 'react-final-form';
import {useDropzone} from 'react-dropzone';
import {Button, Form, Icon, Image, Card} from 'semantic-ui-react';
import createDecorator from 'final-form-calculate';
import {FinalSubmitButton} from 'indico/react/forms';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {Translate, Param} from 'indico/react/i18n';

import './ProfilePicture.module.scss';

function ProfilePictureCard({image, text, email, children, source}) {
  const {
    input: {onChange, value},
  } = useField('source');

  const active = value === source;
  return (
    <Card
      color={active ? 'blue' : null}
      onClick={() => onChange(source)}
      style={active ? {backgroundColor: '#f5f5f5'} : null}
    >
      <Card.Description>
        {image ? (
          <Image src={image} circular size="tiny" />
        ) : (
          <Icon name="question circle outline" size="huge" />
        )}
        {text}
      </Card.Description>
      {email && (
        <Card.Content extra>
          <Translate>
            Based on <Param name="email" value={email} />
          </Translate>
        </Card.Content>
      )}
      {children && <Card.Content extra>{children}</Card.Content>}
    </Card>
  );
}

ProfilePictureCard.propTypes = {
  image: PropTypes.string,
  text: PropTypes.string.isRequired,
  email: PropTypes.string,
  children: PropTypes.node,
  source: PropTypes.oneOf(['standard', 'identicon', 'gravatar', 'custom']).isRequired,
};

ProfilePictureCard.defaultProps = {
  image: null,
  email: null,
  children: null,
};

function CustomPictureUpload({onFileSelected}) {
  const {submitting} = useFormState({
    subscription: {submitting: true},
  });

  const {
    input: {onChange},
  } = useField('file', {allowNull: true});

  const {getRootProps, getInputProps, open} = useDropzone({
    onDropAccepted: ([file]) => {
      onFileSelected(file);
      onChange(file);
    },
    multiple: false,
    noClick: true,
    noKeyboard: true,
    accept: 'image/*',
    disabled: submitting,
  });

  return (
    <section>
      <div {...getRootProps()}>
        <input {...getInputProps()} />
        <Button
          disabled={submitting}
          type="button"
          icon="upload"
          content={Translate.string('Upload')}
          size="small"
          onClick={evt => {
            evt.stopPropagation();
            open();
          }}
        />
      </div>
    </section>
  );
}

CustomPictureUpload.propTypes = {
  onFileSelected: PropTypes.func.isRequired,
};

const formDecorator = createDecorator({
  field: 'file',
  updates: value => (value === null ? {} : {source: 'custom'}),
});

function ProfilePicture({email, current, pictureHash}) {
  const [previewFile, setPreviewFile] = useState(null);
  const [hasPreview, setHasPreview] = useState(pictureHash !== null);

  const submitPicture = async formData => {
    const bodyFormData = new FormData();
    bodyFormData.append('picture', formData.file);
    const config = {
      headers: {'content-type': 'multipart/form-data'},
    };
    try {
      await indicoAxios.post(manageURL({type: formData.source}), bodyFormData, config);
    } catch (e) {
      handleAxiosError(e);
      return;
    }
    setPreviewFile(null);
    setHasPreview(true);
  };

  const getPreview = () => {
    return previewFile ? URL.createObjectURL(previewFile) : pictureURL({slug: 'default'});
  };

  const handleFileSelected = useCallback(file => {
    setPreviewFile(file);
    setHasPreview(true);
  }, []);

  const validate = values => {
    if (values.source === 'custom' && !values.file) {
      return {source: 'invalid'};
    }
    return {};
  };

  return (
    <div styleName="profile-picture-selection">
      <FinalForm
        onSubmit={submitPicture}
        initialValues={{file: null, source: current}}
        validate={validate}
        subscription={{}}
        decorators={[formDecorator]}
      >
        {fprops => (
          <div>
            <Form onSubmit={fprops.handleSubmit}>
              <Card.Group itemsPerRow={4} centered>
                <ProfilePictureCard
                  image={gravatarURL({type: 'standard'})}
                  text={Translate.string('System-assigned icon')}
                  source="standard"
                />
                <ProfilePictureCard
                  image={gravatarURL({type: 'identicon'})}
                  text={Translate.string('Identicon')}
                  source="identicon"
                  email={email}
                />
                <ProfilePictureCard
                  image={gravatarURL({type: 'gravatar'})}
                  text={Translate.string('Gravatar')}
                  source="gravatar"
                  email={email}
                />
                <ProfilePictureCard
                  image={hasPreview ? getPreview() : null}
                  text={Translate.string('Custom picture')}
                  source="custom"
                >
                  <CustomPictureUpload onFileSelected={handleFileSelected} />
                </ProfilePictureCard>
              </Card.Group>
              <FinalSubmitButton
                label={Translate.string('Save changes')}
                className="submit-button"
              />
            </Form>
          </div>
        )}
      </FinalForm>
    </div>
  );
}

ProfilePicture.propTypes = {
  email: PropTypes.string.isRequired,
  current: PropTypes.string.isRequired,
  pictureHash: PropTypes.number,
};

ProfilePicture.defaultProps = {
  pictureHash: null,
};

window.setupPictureSelection = function setupPictureSelection(email, current, pictureHash) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <ProfilePicture email={email} current={current.toLowerCase()} pictureHash={pictureHash} />,
      document.querySelector('#profile-picture-selection')
    );
  });
};
