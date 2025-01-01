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

import {SortableWrapper, useSortableItem} from 'indico/react/sortable';

import FormSection from '../form/FormSection';

import * as actions from './actions';
import FormSectionSetupActions from './FormSectionSetupActions';
import SetupFormItem from './SetupFormItem';

import '../../styles/regform.module.scss';

export default function SetupFormSection({index, ...rest}) {
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
          sortHandle={
            <div className="hide-if-locked" styleName="section-sortable-handle" ref={handleRef} />
          }
          setupActions={<FormSectionSetupActions {...rest} />}
          itemComponent={SetupFormItem}
          itemProps={{sectionId: id}}
          {...rest}
        />
      </SortableWrapper>
    </div>
  );
}

const sectionPropTypes = _.pick(FormSection.propTypes, 'id');

SetupFormSection.propTypes = {
  index: PropTypes.number.isRequired,
  ...sectionPropTypes,
};
