import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const Category = ({title, path, url}) => (
  <>
    <List.Header>
      <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
    </List.Header>
    <List.Description>{path.join(' » ')}</List.Description>
  </>
);

Category.propTypes = {
  title: PropTypes.string.isRequired,
  path: PropTypes.arrayOf(PropTypes.string).isRequired,
  url: PropTypes.string.isRequired,
};
export default Category;
