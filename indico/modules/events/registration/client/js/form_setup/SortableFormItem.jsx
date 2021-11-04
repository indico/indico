// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch} from 'react-redux';

import {useSortableItem} from 'indico/react/sortable';

import FormItem from '../form/FormItem';

import * as actions from './actions';

import '../../styles/regform.module.scss';

export default function SortableFormItem({id, index, sectionId, ...rest}) {
  const dispatch = useDispatch();
  const [handleRef, itemRef, style] = useSortableItem({
    type: `regform-item@${sectionId}`,
    id,
    index,
    separateHandle: true,
    active: rest.isEnabled,
    itemData: {isStaticText: rest.inputType === 'label'},
    moveItem: (sourceIndex, targetIndex) => {
      dispatch(actions.moveItem(sectionId, sourceIndex, targetIndex));
    },
    onDrop: item => {
      if (item.index !== item.originalIndex) {
        dispatch(
          actions.saveItemPosition(
            sectionId,
            item.id,
            item.index,
            item.originalIndex,
            item.isStaticText
          )
        );
      }
    },
  });

  return (
    <div ref={itemRef} style={style}>
      <FormItem
        sortHandle={<div styleName="sortable-handle" ref={handleRef} />}
        id={id}
        {...rest}
      />
    </div>
  );
}

SortableFormItem.propTypes = {
  id: PropTypes.number.isRequired,
  sectionId: PropTypes.number.isRequired,
  inputType: PropTypes.string.isRequired,
  index: PropTypes.number.isRequired,
  ...FormItem.propTypes,
};
