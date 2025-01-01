// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch} from 'react-redux';

import {useSortableItem} from 'indico/react/sortable';

import FormItem from '../form/FormItem';

import * as actions from './actions';
import FormItemSetupActions from './FormItemSetupActions';

import '../../styles/regform.module.scss';

export default function SetupFormItem({index, sectionId, ...rest}) {
  const {id, isEnabled} = rest;
  const dispatch = useDispatch();
  const [handleRef, itemRef, style] = useSortableItem({
    type: `regform-item@${sectionId}`,
    id,
    index,
    separateHandle: true,
    active: isEnabled,
    moveItem: (sourceIndex, targetIndex) => {
      dispatch(actions.moveItem(sectionId, sourceIndex, targetIndex));
    },
    onDrop: item => {
      if (item.index !== item.originalIndex) {
        dispatch(actions.saveItemPosition(sectionId, item.id, item.index, item.originalIndex));
      }
    },
  });

  return (
    <div ref={itemRef} style={style}>
      <FormItem
        sortHandle={<div styleName="sortable-handle" className="hide-if-locked" ref={handleRef} />}
        setupActions={<FormItemSetupActions {...rest} />}
        {...rest}
      />
    </div>
  );
}

const itemPropTypes = _.pick(
  FormItem.propTypes,
  'inputType',
  'isEnabled',
  ...Object.keys(FormItemSetupActions.propTypes)
);

SetupFormItem.propTypes = {
  sectionId: PropTypes.number.isRequired,
  index: PropTypes.number.isRequired,
  ...itemPropTypes,
};

SetupFormItem.defaultProps = _.pick(FormItem.defaultProps, Object.keys(itemPropTypes));
