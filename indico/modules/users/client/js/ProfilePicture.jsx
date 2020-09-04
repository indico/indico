// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageURL from 'indico-url:users.manage_profile_picture';
import pictureURL from 'indico-url:users.profile_picture_display';
import gravatarURL from 'indico-url:users.profile_picture_gravatar';

import React, {useState, useCallback, useRef} from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import {Form as FinalForm, Field} from 'react-final-form';
import Dropzone from 'react-dropzone';
import {Button, Form, Icon, Image, Card} from 'semantic-ui-react';
import {FinalSubmitButton} from 'indico/react/forms';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {Translate, Param} from 'indico/react/i18n';

import './ProfilePicture.module.scss';

function ProfilePicture({email, current, pictureHash}) {
  const [previewFile, setPreviewFile] = useState(null);
  const [hasPreview, setHasPreview] = useState(pictureHash !== null);
  const [loading, setLoading] = useState(false);

  const submitPicture = async formData => {
    setLoading(true);
    const bodyFormData = new FormData();
    bodyFormData.append('picture', formData.file);
    const config = {
      headers: {'content-type': 'multipart/form-data'},
    };
    try {
      await indicoAxios.post(manageURL({type: formData.option}), bodyFormData, config);
    } catch (e) {
      handleAxiosError(e);
      setLoading(false);
      return;
    }
    setPreviewFile(null);
    setLoading(false);
    setHasPreview(true);
  };

  const getPreview = () => {
    return previewFile ? URL.createObjectURL(previewFile) : pictureURL({slug: 'default'});
  };

  const onDrop = useCallback(acceptedFiles => {
    setPreviewFile(acceptedFiles[0]);
    setHasPreview(true);
  }, []);

  const dropzoneRef = useRef();

  const openDialog = () => {
    // Note that the ref is set async, so it might be null at some point
    if (dropzoneRef.current) {
      dropzoneRef.current.open();
    }
  };

  return (
    <div styleName="profile-picture-selection">
      <FinalForm
        onSubmit={submitPicture}
        initialValues={{file: null, option: current}}
        subscription={{values: true}}
        mutators={{
          setFile: ([file], state, utils) => {
            utils.changeValue(state, 'file', () => file);
          },
          setOption: ([option], state, utils) => {
            utils.changeValue(state, 'option', () => option);
          },
        }}
      >
        {fprops => (
          <div>
            <Form onSubmit={fprops.handleSubmit}>
              <Card.Group itemsPerRow={4} centered>
                <Card
                  color={fprops.values.option === 'standard' ? 'blue' : null}
                  onClick={() => fprops.form.mutators.setOption('standard')}
                  style={fprops.values.option === 'standard' ? {backgroundColor: '#f5f5f5'} : null}
                >
                  <Card.Description>
                    <Image src={gravatarURL({type: 'standard'})} circular size="tiny" />
                    <Translate> System assigned profile picture</Translate>
                  </Card.Description>
                </Card>
                <Card
                  color={fprops.values.option === 'identicon' ? 'blue' : null}
                  onClick={() => fprops.form.mutators.setOption('identicon')}
                  style={fprops.values.option === 'identicon' ? {backgroundColor: '#f5f5f5'} : null}
                >
                  <Card.Description>
                    <Image src={gravatarURL({type: 'identicon'})} circular size="tiny" />
                    Identicon
                  </Card.Description>
                  <Card.Content extra>
                    <Translate>
                      Based on <Param name="email" value={email} />
                    </Translate>
                  </Card.Content>
                </Card>
                <Card
                  color={fprops.values.option === 'gravatar' ? 'blue' : null}
                  onClick={() => fprops.form.mutators.setOption('gravatar')}
                  style={fprops.values.option === 'gravatar' ? {backgroundColor: '#f5f5f5'} : null}
                >
                  <Card.Description>
                    <Image src={gravatarURL({type: 'gravatar'})} circular size="tiny" />
                    Gravatar
                  </Card.Description>
                  <Card.Content extra>
                    <Translate>
                      Based on <Param name="email" value={email} />
                    </Translate>
                  </Card.Content>
                </Card>
                <Card
                  color={fprops.values.option === 'custom' ? 'blue' : null}
                  onClick={() => fprops.form.mutators.setOption('custom')}
                  style={fprops.values.option === 'custom' ? {backgroundColor: '#f5f5f5'} : null}
                >
                  <Card.Description>
                    {hasPreview ? (
                      <Image src={getPreview()} circular size="tiny" />
                    ) : (
                      <Icon name="question circle outline" size="huge" />
                    )}

                    <Translate>Custom picture</Translate>
                  </Card.Description>
                  <Card.Content extra>
                    <Dropzone
                      ref={dropzoneRef}
                      onDrop={acceptedFiles => {
                        onDrop(acceptedFiles);
                        fprops.form.mutators.setFile(acceptedFiles[0]);
                        fprops.form.mutators.setOption('custom');
                      }}
                      multiple={false}
                      noClick
                      noKeyboard
                      accept="image/*"
                    >
                      {({getRootProps, getInputProps}) => (
                        <section>
                          <div {...getRootProps()}>
                            <input {...getInputProps()} />
                            <Button
                              disabled={loading}
                              type="button"
                              icon="upload"
                              content={Translate.string('Upload')}
                              size="small"
                              onClick={e => {
                                e.stopPropagation();
                                openDialog();
                              }}
                            />
                          </div>
                        </section>
                      )}
                    </Dropzone>
                    <Field name="file" render={() => null} />
                    <Field name="option" render={() => null} />
                  </Card.Content>
                </Card>
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
