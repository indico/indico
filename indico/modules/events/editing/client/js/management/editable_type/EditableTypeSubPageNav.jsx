// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableTypeURL from 'indico-url:event_editing.manage_editable_type';

import PropTypes from 'prop-types';
import React from 'react';
import {useParams} from 'react-router-dom';

import {
  ManagementPageBackButton,
  ManagementPageTitle,
  ManagementPageSubTitle,
} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import {EditableTypeTitles} from '../../models';

export default function EditableTypeSubPageNav({title}) {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();
  return (
    <>
      <ManagementPageTitle
        title={Translate.string('Editing ({type})', {type: EditableTypeTitles[type]})}
      />
      <ManagementPageSubTitle title={title} />
      <ManagementPageBackButton url={editableTypeURL({event_id: eventId, type})} />
    </>
  );
}

EditableTypeSubPageNav.propTypes = {
  title: PropTypes.string.isRequired,
};
