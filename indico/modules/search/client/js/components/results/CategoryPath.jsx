import React from 'react';
import PropTypes from 'prop-types';
import {Breadcrumb} from 'semantic-ui-react';

import './CategoryPath.module.scss';

export default function CategoryPath({path}) {
  const sections = path.map(item => ({
    key: item.id,
    href: item.url,
    content: item.title,
  }));

  return <Breadcrumb styleName="path" divider="»" sections={sections} />;
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
