// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Breadcrumb, Icon} from 'semantic-ui-react';

import './Path.module.scss';

export const pathPropType = PropTypes.arrayOf(
  PropTypes.shape({
    type: PropTypes.string.isRequired,
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
  })
);

export function Path({path}) {
  const sections = path.map(item => ({
    key: `${item.type}-${item.id}`,
    href: item.url,
    content: item.title,
  }));

  return (
    <span styleName="path">
      <Icon name="sitemap" />
      <Breadcrumb divider="»" sections={sections} />
    </span>
  );
}

Path.propTypes = {
  path: pathPropType.isRequired,
};
