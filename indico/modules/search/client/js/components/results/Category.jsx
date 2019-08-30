import React from 'react';
import {List, Breadcrumb} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './Category.module.scss';

const Category = ({title, path, url}) => {
  const array = path.slice(0, path.length - 1);

  return (
    <>
      <List.Header>
        <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
      </List.Header>
      {path.length !== 0 && (
        <List.Description>
          <span>&nbsp;</span>
          <Breadcrumb>
            {array.map(item => (
              <Breadcrumb.Section key={item}>
                <span styleName="category">
                  <a href="https://www.google.com">
                    {item}
                    <span>&nbsp;</span>
                  </a>
                  {' » '}
                  <span>&nbsp;</span>
                </span>
              </Breadcrumb.Section>
            ))}
            <Breadcrumb.Section active styleName="category">
              {path[path.length - 1]}
            </Breadcrumb.Section>
          </Breadcrumb>
        </List.Description>
      )}
    </>
  );
};

Category.propTypes = {
  title: PropTypes.string.isRequired,
  path: PropTypes.arrayOf(PropTypes.string).isRequired,
  url: PropTypes.string.isRequired,
};
export default Category;
