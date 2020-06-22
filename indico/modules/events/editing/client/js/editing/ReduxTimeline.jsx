// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableDetailsURL from 'indico-url:event_editing.api_editable';
import tagsURL from 'indico-url:event_editing.api_tags';

import React from 'react';
import {useParams} from 'react-router-dom';
import {Provider} from 'react-redux';
import {Loader} from 'semantic-ui-react';
import createReduxStore from 'indico/utils/redux';
import {useNumericParam} from 'indico/react/util/routing';
import {useIndicoAxios} from 'indico/react/hooks';

import Timeline from './timeline';
import reducer from './timeline/reducer';

export default function ReduxTimeline() {
  const eventId = useNumericParam('confId');
  const contributionId = useNumericParam('contrib_id');
  const {type: editableType} = useParams();

  const {data: fileTypes, loading: isLoadingFileTypes} = useIndicoAxios({
    url: fileTypesURL({confId: eventId, type: editableType}),
    camelize: true,
    trigger: [eventId, editableType],
  });

  const {data: tags, loading: isLoadingTags} = useIndicoAxios({
    url: tagsURL({confId: eventId}),
    camelize: true,
    trigger: [eventId],
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
          confId: eventId,
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
