// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {List, Pagination, Placeholder, Segment} from 'semantic-ui-react';

import {useResponsive} from 'indico/react/util';

import './ResultList.module.scss';

export default function ResultList({
  component: Component,
  page,
  numPages,
  data,
  loading,
  onPageChange,
  showCategoryPath,
}) {
  const {isWideScreen} = useResponsive();

  return (
    <>
      <Segment>
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
      {numPages > 1 && (
        <div styleName="pagination">
          <Pagination
            activePage={page}
            onPageChange={(e, {activePage}) => onPageChange(activePage)}
            totalPages={numPages}
            boundaryRange={isWideScreen ? 1 : 0}
            siblingRange={isWideScreen ? 2 : 1}
          />
        </div>
      )}
    </>
  );
}

ResultList.propTypes = {
  component: PropTypes.elementType.isRequired,
  page: PropTypes.number.isRequired,
  numPages: PropTypes.number.isRequired,
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  loading: PropTypes.bool.isRequired,
  onPageChange: PropTypes.func.isRequired,
  showCategoryPath: PropTypes.bool.isRequired,
};
