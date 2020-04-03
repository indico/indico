// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableTypeURL from 'indico-url:event_editing.manage_editable_type';

import React from 'react';
import PropTypes from 'prop-types';
import {useParams} from 'react-router-dom';

import {useNumericParam} from 'indico/react/util/routing';
import {
  ManagementPageBackButton,
  ManagementPageTitle,
  ManagementPageSubTitle,
} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {EditableTypeTitles} from '../models';

export default function EditingTypeSubPageNav({title}) {
  const eventId = useNumericParam('confId');
  const {type} = useParams();
  return (
    <>
      <ManagementPageTitle
        title={Translate.string('Editing ({type})', {type: EditableTypeTitles[type]})}
      />
      <ManagementPageSubTitle title={title} />
      <ManagementPageBackButton url={editableTypeURL({confId: eventId, type})} />
    </>
  );
}

EditingTypeSubPageNav.propTypes = {
  title: PropTypes.string.isRequired,
};
