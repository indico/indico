// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {List, Menu, Pagination, Placeholder, Segment} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {useResponsive} from 'indico/react/util';

import './ResultList.module.scss';

export default function ResultList({
  component: Component,
  page,
  numPages,
  pageNav,
  data,
  loading,
  onPageChange,
  showCategoryPath,
}) {
  const {isWideScreen} = useResponsive();

  return (
    <>
      <Segment id="search-results" role="tabpanel">
        <List divided relaxed stylename="space">
          {loading ? (
            <Placeholder>
              <Placeholder.Paragraph>
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
              </Placeholder.Paragraph>
              <Placeholder.Paragraph>
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
              </Placeholder.Paragraph>
              <Placeholder.Paragraph>
                <Placeholder.Line />
                <Placeholder.Line />
                <Placeholder.Line />
              </Placeholder.Paragraph>
            </Placeholder>
          ) : (
            data.map(item => (
              <List.Item key={nanoid()}>
                <List.Content>
                  <Component {...item} showCategoryPath={showCategoryPath} />
                </List.Content>
              </List.Item>
            ))
          )}
        </List>
      </Segment>
      {pageNav && (pageNav.next !== null || pageNav.prev !== null) ? (
        <div styleName="pagination">
          <Menu pagination>
            <Menu.Item disabled={pageNav.prev === null} onClick={() => onPageChange(pageNav.prev)}>
              <Translate>⟨ Previous page</Translate>
            </Menu.Item>
            <Menu.Item disabled={pageNav.next === null} onClick={() => onPageChange(pageNav.next)}>
              <Translate>Next page ⟩</Translate>
            </Menu.Item>
          </Menu>
        </div>
      ) : numPages > 1 ? (
        <div styleName="pagination">
          <Pagination
            activePage={page}
            onPageChange={(e, {activePage}) => onPageChange(activePage)}
            totalPages={numPages}
            boundaryRange={isWideScreen ? 1 : 0}
            siblingRange={isWideScreen ? 2 : 1}
          />
        </div>
      ) : null}
    </>
  );
}

ResultList.propTypes = {
  component: PropTypes.elementType.isRequired,
  page: PropTypes.number.isRequired,
  numPages: PropTypes.number.isRequired,
  pageNav: PropTypes.shape({
    prev: PropTypes.number,
    next: PropTypes.number,
  }),
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  loading: PropTypes.bool.isRequired,
  onPageChange: PropTypes.func.isRequired,
  showCategoryPath: PropTypes.bool.isRequired,
};

ResultList.defaultProps = {
  pageNav: null,
};
