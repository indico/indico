// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form, Message} from 'semantic-ui-react';

import {Translate, Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';

import {FinalFileManager} from '../FileManager';
import * as selectors from '../selectors';

export default function UpdateFilesBox({visible, mustChange, requirePublishable}) {
  const lastRevisionWithFiles = useSelector(selectors.getLastRevisionWithFiles);
  const staticData = useSelector(selectors.getStaticData);
  const {eventId, contributionId, editableType} = staticData;
  const fileTypes = useSelector(selectors.getFileTypes);
  const publishableFileTypes = useSelector(selectors.getPublishableFileTypes);

  return (
    <Form.Field style={{display: !visible ? 'none' : undefined}}>
      <FinalFileManager
        name="files"
        fileTypes={fileTypes}
        files={lastRevisionWithFiles.files}
        uploadURL={uploadURL({
          event_id: eventId,
          contrib_id: contributionId,
          type: editableType,
        })}
        mustChange={mustChange}
      />
      <Field name="files" subscription={{value: true}}>
        {({input: {value: currentFiles}}) => {
          if (
            !requirePublishable ||
            publishableFileTypes.some(fileType => fileType.id in currentFiles)
          ) {
            return null;
          }
          return (
            <>
              <Message visible warning>
                <PluralTranslate count={publishableFileTypes.length}>
                  <Singular>
                    There are no publishable files. Please upload a{' '}
                    <Param
                      name="types"
                      wrapper={<strong />}
                      value={publishableFileTypes.map(ft => ft.name).join(', ')}
                    />{' '}
                    file.
                  </Singular>
                  <Plural>
                    There are no publishable files. Please upload a file in at least one of the
                    following types:{' '}
                    <Param
                      name="types"
                      wrapper={<strong />}
                      value={publishableFileTypes.map(ft => ft.name).join(', ')}
                    />
                  </Plural>
                </PluralTranslate>
              </Message>
              <Field
                name="_nopublishables"
                validate={() => Translate.string('There is no publishable file uploaded.')}
                render={() => null}
              />
            </>
          );
        }}
      </Field>
    </Form.Field>
  );
}

UpdateFilesBox.propTypes = {
  visible: PropTypes.bool.isRequired,
  mustChange: PropTypes.bool.isRequired,
  requirePublishable: PropTypes.bool.isRequired,
};
