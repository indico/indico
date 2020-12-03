// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Breadcrumb, Icon} from 'semantic-ui-react';

import './CategoryPath.module.scss';

export default function CategoryPath({path}) {
  const sections = path.map(item => ({
    key: item.id,
    href: item.url,
    content: item.title,
  }));

  return (
    <>
      <Icon name="sitemap" />
      <Breadcrumb styleName="path" divider="»" sections={sections} />
    </>
  );
}

CategoryPath.propTypes = {
  path: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      url: PropTypes.string.isRequired,
    })
  ).isRequired,
};
