// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch} from 'react-redux';

import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import FormSection from '../form/FormSection';

import * as actions from './actions';
import SortableFormItem from './SortableFormItem';

export default function SortableFormSection({index, ...rest}) {
  const {id} = rest;
  const dispatch = useDispatch();
  const [handleRef, itemRef, style] = useSortableItem({
    type: 'regform-section',
    id,
    index,
    separateHandle: true,
    moveItem: (sourceIndex, targetIndex) => {
      dispatch(actions.moveSection(sourceIndex, targetIndex));
    },
    onDrop: item => {
      if (item.index !== item.originalIndex) {
        dispatch(actions.saveSectionPosition(item.id, item.index, item.originalIndex));
      }
    },
  });

  return (
    <div ref={itemRef} style={style}>
      <SortableWrapper accept={`regform-item@${id}`}>
        <FormSection
          sortHandle={<div className="section-sortable-handle hide-if-locked" ref={handleRef} />}
          ItemComponent={SortableFormItem}
          itemProps={{sectionId: id}}
          {...rest}
        />
      </SortableWrapper>
    </div>
  );
}

const sectionPropTypes = _.pick(FormSection.propTypes, 'id');

SortableFormSection.propTypes = {
  index: PropTypes.number.isRequired,
  ...sectionPropTypes,
};
