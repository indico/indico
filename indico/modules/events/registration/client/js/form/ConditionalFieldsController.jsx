// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {useEffect} from 'react';
import {useFormState} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';

import {setHiddenItemIds} from '../form_submission/actions';

import {getHiddenItemIds, getItems} from './selectors';

function parseConditionalValues(value) {
  // TODO move this logic to the field implementations
  if (typeof value === 'boolean') {
    return value ? ['1'] : ['0'];
  } else if (value !== null && typeof value === 'object') {
    if (value.choice) {
      return [value.choice];
    }
    return Object.entries(value)
      .filter(([, slots]) => slots > 0)
      .map(([key]) => key);
  }
  return value || undefined;
}

export default function ConditionalFieldsController() {
  const {values} = useFormState({subscription: {values: true}});
  const dispatch = useDispatch();
  const fields = useSelector(getItems);
  const currentlyHiddenItemIds = useSelector(getHiddenItemIds);

  const hiddenItemIds = Object.values(fields)
    .filter(field => field.showIfFieldId)
    .map(field => {
      const conditionalField = fields[field.showIfFieldId];
      const conditionalValues = parseConditionalValues(values[conditionalField.htmlName]);
      const hidden =
        currentlyHiddenItemIds.includes(conditionalField.id) ||
        !conditionalValues?.some(value => field.showIfFieldValues.includes(value));
      return hidden ? field.id : null;
    })
    .filter(id => id !== null);

  useEffect(() => {
    if (!_.isEqual(currentlyHiddenItemIds, hiddenItemIds)) {
      dispatch(setHiddenItemIds(hiddenItemIds));
    }
  }, [dispatch, currentlyHiddenItemIds, hiddenItemIds]);
  return null;
}
