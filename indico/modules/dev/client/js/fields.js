// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:dev.test_upload';

import {
  FinalDatePeriod,
  FinalEmailList,
  FinalLocationField,
  FinalItemList,
  FinalPictureManager,
  FinalSessionColorPicker,
  FinalSingleDatePicker,
  FinalSingleFileManager,
  FinalTinyMCETextEditor,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalMarkdownEditor} from 'indico/react/components/MarkdownEditor';
import {
  FinalAbstractPersonLinkField,
  FinalContributionPersonLinkField,
  FinalPersonLinkField,
} from 'indico/react/components/PersonLinkField';
import {FinalRating} from 'indico/react/components/ReviewRating';

const getFields = () => {
  const personLinkFieldExtraOptions = {
    eventId: 1,
    sessionUser: {...Indico.User, favoriteUsers: {}}, // clean up the user object
    emptyMessage: null,
    hasPredefinedAffiliations: false,
    canEnterManually: true,
    defaultSearchExternal: false,
    nameFormat: '',
  };

  return [
    {title: 'Review rating', component: FinalRating, initialValue: 0, min: 0, max: 5},
    {title: 'Email list', component: FinalEmailList, initialValue: []},
    {
      title: 'Single date picker',
      component: FinalSingleDatePicker,
      asRange: false,
      yearsBefore: 5,
      yearsAfter: 5,
    },
    {
      title: 'Date period',
      component: FinalDatePeriod,
      initialValue: {},
      readOnly: false,
      minimumDays: 1,
    },
    {title: 'Single file manager', component: FinalSingleFileManager, uploadURL: uploadURL()},
    {
      title: 'Picture manager',
      component: FinalPictureManager,
      uploadURL: uploadURL(),
      previewURL: '/',
    },
    {
      title: 'Person link field',
      component: FinalPersonLinkField,
      initialValue: [],
      ...personLinkFieldExtraOptions,
      roles: [],
    },
    {
      title: 'Person link field (abstracts)',
      component: FinalAbstractPersonLinkField,
      initialValue: [],
      ...personLinkFieldExtraOptions,
      allowSpeakers: true,
    },
    {
      title: 'Person link field (contributions)',
      component: FinalContributionPersonLinkField,
      initialValue: [],
      ...personLinkFieldExtraOptions,
      allowAuthors: true,
      allowSubmitters: true,
      defaultIsSubmitter: true,
    },
    {title: 'TinyMCE text editor', component: FinalTinyMCETextEditor, loading: false},
    {title: 'Markdown editor', component: FinalMarkdownEditor},
    {
      title: 'Location field',
      component: FinalLocationField,
      initialValue: {},
      editAddress: true,
      parent: {
        title: 'A Conference test',
        type: 'Event',
        location_data: {
          venue_id: 1,
          venue_name: 'CERN',
          room_id: 1,
          room_name: 'Main Auditorium',
          address: 'Geneva, Switzerland',
        },
      },
    },
    {title: 'Session color picker', component: FinalSessionColorPicker, initialValue: {}},
    {
      title: 'Item list field',
      component: FinalItemList,
      initialValue: [],
      itemShape: [
        {name: 'name', title: 'Name', fieldProps: {type: 'text'}},
        {name: 'value', title: 'Value', fieldProps: {type: 'text'}},
      ],
      sortable: false,
      canDisableItem: true,
    },
    {
      title: 'References field',
      component: FinalReferences,
      initialValue: [],
    },
    {
      title: 'Tag list',
      component: FinalTagList,
      initialValue: [],
      placeholder: 'Please enter a keyword',
    },
  ];
};

export default getFields;
