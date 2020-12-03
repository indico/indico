// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List, Placeholder, Segment} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './ResultList.module.scss';
import SearchPagination from './SearchPagination';

export default function ResultList({
  component: Component,
  page,
  numPages,
  data,
  loading,
  onPageChange,
}) {
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
              <List.Item key={item.id}>
                <List.Content styleName="list">
                  <Component {...item} />
                </List.Content>
              </List.Item>
            ))
          )}
        </List>
      </Segment>
      {numPages > 1 && (
        <SearchPagination activePage={page} numOfPages={numPages} onPageChange={onPageChange} />
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
};
