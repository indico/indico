import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';

const Category = ({name, path}) => (
  <>
    <List.Header>{name}</List.Header>
    <List.Description>{path.join(' >> ')}</List.Description>
  </>
);

Category.propTypes = {
  name: PropTypes.string.isRequired,
  path: PropTypes.arrayOf(PropTypes.string).isRequired,
};
export default Category;
