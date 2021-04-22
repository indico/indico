// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchURL from 'indico-url:search.api_search';

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState} from 'react';
import {Grid, Loader, Menu, Message} from 'semantic-ui-react';

import {useIndicoAxios, useQueryParams} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';

import ResultList from './ResultList';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import EventNote from './results/EventNote';
import File from './results/File';
import SearchBar from './SearchBar';
import SideBar from './SideBar';

import './SearchApp.module.scss';

function useSearch(url, query) {
  const [page, setPage] = useState(1);

  const {data, loading, lastData} = useIndicoAxios({
    url,
    camelize: true,
    options: {params: {...query, page}},
    forceDispatchEffect: () => query?.q,
    trigger: [url, query, page],
    customHandler: undefined,
  });

  useEffect(() => {
    setPage(1);
  }, [query]);

  return [
    useMemo(
      () => ({
        page,
        pages: data?.pages || 1,
        total: data?.total || 0,
        data: data?.results || [],
        aggregations: data?.aggregations || lastData?.aggregations || [],
        loading,
      }),
      [page, data, lastData, loading]
    ),
    setPage,
  ];
}

function SearchTypeMenuItem({index, active, title, total, loading, onClick}) {
  let indicator = null;
  if (loading) {
    indicator = <Loader active inline size="tiny" style={{zIndex: 'unset'}} />;
  } else if (total !== -1) {
    indicator = ` (${total})`;
  }
  return (
    <Menu.Item index={index} active={active} onClick={onClick} disabled={loading || !total}>
      {title}
      {indicator}
    </Menu.Item>
  );
}

SearchTypeMenuItem.propTypes = {
  index: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  active: PropTypes.bool,
  total: PropTypes.number,
  loading: PropTypes.bool,
  onClick: PropTypes.func,
};

SearchTypeMenuItem.defaultProps = {
  total: 0,
  active: false,
  loading: false,
  onClick: undefined,
};

function NoResults({query}) {
  return (
    <Message warning={!!query}>
      {query ? (
        <>
          <Message.Header>
            <Translate>No Results</Translate>
          </Message.Header>
          <Translate>
            Your search - <Param name="query" value={query} /> - did not match any results
          </Translate>
        </>
      ) : (
        <Translate>Please enter a term above to begin searching</Translate>
      )}
    </Message>
  );
}

NoResults.propTypes = {
  query: PropTypes.string.isRequired,
};

export default function SearchApp() {
  const [query, setQuery] = useQueryParams();
  const [activeMenuItem, setActiveMenuItem] = useState(undefined);
  const {q, ...filters} = query;
  const [categoryResults, setCategoryPage] = useSearch(searchURL({type: 'category'}), query);
  const [eventResults, setEventPage] = useSearch(searchURL({type: 'event'}), query);
  const [contributionResults, setContributionPage] = useSearch(
    searchURL({type: 'contribution'}),
    query
  );
  const [fileResults, setFilePage] = useSearch(searchURL({type: 'attachment'}), query);
  const [noteResults, setNotePage] = useSearch(searchURL({type: 'event_note'}), query);
  const searchMap = [
    [Translate.string('Categories'), categoryResults, setCategoryPage, Category],
    [Translate.string('Events'), eventResults, setEventPage, Event],
    [Translate.string('Contributions'), contributionResults, setContributionPage, Contribution],
    [Translate.string('Materials'), fileResults, setFilePage, File],
    [Translate.string('Notes'), noteResults, setNotePage, EventNote],
  ];
  // Defaults to the first tab loading or with results
  const menuItem =
    activeMenuItem || Math.max(0, searchMap.findIndex(x => x[1].loading || x[1].total));
  // eslint-disable-next-line no-unused-vars
  const [_, results, setPage, Component] = searchMap[menuItem];
  const isAnyLoading = searchMap.some(x => x[1].loading);

  const handleQuery = (value, type = 'q') => setQuery(type, value, type === 'q');

  return (
    <Grid columns={2} doubling padded styleName="grid">
      {results.aggregations.length > 0 && (
        <Grid.Column width={3} only="large screen">
          <SideBar query={filters} aggregations={results.aggregations} onChange={handleQuery} />
        </Grid.Column>
      )}
      <Grid.Column width={7}>
        <SearchBar onSearch={handleQuery} searchTerm={q || ''} />
        <Menu pointing secondary styleName="menu">
          {searchMap.map(([label, _results], idx) => (
            <SearchTypeMenuItem
              key={label}
              index={idx}
              active={menuItem === idx}
              title={label}
              total={_results.total}
              loading={_results.loading}
              onClick={(e, {index}) => setActiveMenuItem(index)}
            />
          ))}
        </Menu>
        {q && (results.total || isAnyLoading) ? (
          <ResultList
            component={Component}
            page={results.page}
            numPages={results.pages}
            data={results.data}
            onPageChange={setPage}
            loading={results.loading}
          />
        ) : (
          <NoResults query={q} />
        )}
      </Grid.Column>
    </Grid>
  );
}
