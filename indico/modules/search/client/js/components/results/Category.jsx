import React from 'react';
import {List, Breadcrumb} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './Category.module.scss';

const Category = ({title, path, url}) => {
  const array = path.slice(0, path.length - 1);

  return (
    <div styleName="category">
      <List.Header>
        <a href={`https://blackhole.cern.ch${url}`}>{title}</a>
      </List.Header>
      <div styleName="description">
        {path.length !== 0 && (
          <List.Description>
            <Breadcrumb>
              {array.map(item => (
                <Breadcrumb.Section key={item} styleName="list">
                  <a href="https://www.google.com">
                    {item}
                    <span>&nbsp;</span>
                  </a>
                  {' » '}
                  <span>&nbsp;</span>
                </Breadcrumb.Section>
              ))}
              <Breadcrumb.Section active styleName="list">
                <a href="https://www.google.com">
                  {path[path.length - 1]}
                  <span>&nbsp;</span>
                </a>
              </Breadcrumb.Section>
            </Breadcrumb>
          </List.Description>
        )}
      </div>
    </div>
  );
};

Category.propTypes = {
  title: PropTypes.string.isRequired,
  path: PropTypes.arrayOf(PropTypes.string).isRequired,
  url: PropTypes.string.isRequired,
};
export default Category;
