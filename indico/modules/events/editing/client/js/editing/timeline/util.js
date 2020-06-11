// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';

import {filePropTypes} from './FileManager/util';

export const userPropTypes = {
  identifier: PropTypes.string.isRequired,
  fullName: PropTypes.string.isRequired,
  avatarBgColor: PropTypes.string.isRequired,
  id: PropTypes.number.isRequired,
};

const statePropTypes = {
  cssClass: PropTypes.string,
  name: PropTypes.string.isRequired,
  title: PropTypes.string,
};

export const blockItemPropTypes = {
  id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
  createdDt: PropTypes.string.isRequired,
  modifiedDt: PropTypes.string,
  user: PropTypes.shape(userPropTypes),
  text: PropTypes.string,
  html: PropTypes.string,
  internal: PropTypes.bool,
  system: PropTypes.bool,
};

export const blockPropTypes = {
  id: PropTypes.number.isRequired,
  files: PropTypes.arrayOf(PropTypes.shape(filePropTypes)).isRequired,
  submitter: PropTypes.shape(userPropTypes).isRequired,
  editor: PropTypes.shape(userPropTypes),
  createdDt: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.shape(blockItemPropTypes)).isRequired,
  initialState: PropTypes.shape(statePropTypes).isRequired,
  finalState: PropTypes.shape(statePropTypes).isRequired,
  comment: PropTypes.string.isRequired,
  commentHtml: PropTypes.string.isRequired,
};
