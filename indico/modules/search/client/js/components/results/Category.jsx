import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const Category = ({title, path}) => (
  <>
    <List.Header>{title}</List.Header>
    <List.Description>{path.join(' >> ')}</List.Description>
  </>
);

Category.propTypes = {
  title: PropTypes.string.isRequired,
  path: PropTypes.arrayOf(PropTypes.string).isRequired,
};
export default Category;
