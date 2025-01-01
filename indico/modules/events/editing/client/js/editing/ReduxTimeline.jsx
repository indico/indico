// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableDetailsURL from 'indico-url:event_editing.api_editable';
import fileTypesURL from 'indico-url:event_editing.api_file_types';
import tagsURL from 'indico-url:event_editing.api_tags';

import React from 'react';
import {Provider} from 'react-redux';
import {useParams} from 'react-router-dom';
import {Loader} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {useNumericParam} from 'indico/react/util/routing';
import createReduxStore from 'indico/utils/redux';

import Timeline from './timeline';
import reducer from './timeline/reducer';

export default function ReduxTimeline() {
  const eventId = useNumericParam('event_id');
  const contributionId = useNumericParam('contrib_id');
  const {type: editableType} = useParams();

  const {data: fileTypes, loading: isLoadingFileTypes} = useIndicoAxios(
    fileTypesURL({event_id: eventId, type: editableType}),
    {camelize: true}
  );

  const {data: tags, loading: isLoadingTags} = useIndicoAxios(tagsURL({event_id: eventId}), {
    camelize: true,
  });

  if (isLoadingFileTypes || isLoadingTags) {
    return <Loader inline="centered" active />;
  } else if (!fileTypes || !tags) {
    return null;
  }

  const store = createReduxStore(
    'editing-timeline',
    {timeline: reducer},
    {
      staticData: {
        eventId,
        contributionId,
        editableType,
        fileTypes,
        tags,
        editableDetailsURL: editableDetailsURL({
          event_id: eventId,
          contrib_id: contributionId,
          type: editableType,
        }),
      },
    }
  );
  return (
    <Provider store={store}>
      <Timeline />
    </Provider>
  );
}
