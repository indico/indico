// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryURL from 'indico-url:categories.display';

import PropTypes from 'prop-types';
import React from 'react';
import {Breadcrumb, Icon} from 'semantic-ui-react';

import './CategoryPath.module.scss';

export default function CategoryPath({path}) {
  const sections = path.map(item => ({
    key: item.id,
    href: categoryURL({category_id: item.id}),
    content: item.title,
  }));

  return (
    <span styleName="category-path">
      <Icon name="sitemap" />
      <Breadcrumb divider="»" sections={sections} />
    </span>
  );
}

CategoryPath.propTypes = {
  path: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
    })
  ).isRequired,
};
