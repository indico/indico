// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchCategoriesURL from 'indico-url:search.search_categories';
import searchContributionsURL from 'indico-url:search.search_contributions';
import searchEventsURL from 'indico-url:search.search_events';
import searchFilesURL from 'indico-url:search.search_files';

import PropTypes from 'prop-types';
import React, {useEffect, useReducer, useState, useMemo} from 'react';
import {Loader, Menu, Grid} from 'semantic-ui-react';
import {useQueryParam, StringParam} from 'use-query-params';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import ResultList from './ResultList';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import File from './results/File';
import NoResults from './results/NoResults';
import SearchBar from './SearchBar';
import SideBar from './SideBar';

const searchReducer = (state, action) => {
  switch (action.type) {
    case 'SET_QUERY':
      return {...state, query: action.query, page: 1};
    case 'SET_PAGE':
      return {...state, page: action.page};
    default:
      throw new Error(`invalid action: ${action.type}`);
  }
};

function useSearch(url, outerQuery) {
  const [{query, page}, dispatch] = useReducer(searchReducer, {query: '', page: 1});
  useEffect(() => {
    // we have to dispatch an action that sets the query and resets the page.
    // since the axios hook only monitors `query` the request won't be sent
    // until the reducer ran and updated both query and page
    dispatch({type: 'SET_QUERY', query: outerQuery});
  }, [outerQuery]);

  const {data, error, loading} = useIndicoAxios({
    url,
    camelize: true,
    options: {params: {q: query, page}},
    forceDispatchEffect: () => !!query,
    trigger: [url, query, page],
  });

  const setPage = newPage => {
    dispatch({type: 'SET_PAGE', page: newPage});
  };

  return [
    useMemo(
      () => ({
        page: data?.page || 1,
        pages: data?.pages || 1,
        total: data?.total || 0,
        data: data?.results || [],
        // ensure the initial state is loading, as the data is undefined
        loading: (!data && !error) || loading,
      }),
      [data, error, loading]
    ),
    setPage,
  ];
}

function SearchTypeMenuItem({index, active, title, total, loading, onClick}) {
  let indicator = null;
  if (loading) {
    indicator = <Loader active inline size="tiny" />;
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

export default function SearchApp() {
  const [query, setQuery] = useQueryParam('q', StringParam);
  const [activeMenuItem, setActiveMenuItem] = useState(0);
  const handleClick = (e, {index}) => {
    setActiveMenuItem(index);
  };

  const [categoryResults, setCategoryPage] = useSearch(searchCategoriesURL(), query);
  const [eventResults, setEventPage] = useSearch(searchEventsURL(), query);
  const [contributionResults, setContributionPage] = useSearch(searchContributionsURL(), query);
  const [fileResults, setFilePage] = useSearch(searchFilesURL(), query);
  const searchMap = [
    ['Categories', categoryResults, setCategoryPage, Category],
    ['Events', eventResults, setEventPage, Event],
    ['Contributions', contributionResults, setContributionPage, Contribution],
    ['Materials', fileResults, setFilePage, File],
  ];
  // eslint-disable-next-line no-unused-vars
  const [_, results, setPage, Component] = searchMap[activeMenuItem];
  const isAnyLoading = searchMap.some(x => x[1].loading);

  // On every search, the tab will be either the first loading or with results
  const menuItem = searchMap.findIndex(x => x[1].loading || x[1].total > 0);
  // TODO: we could make this initially uncontrolled, but if the user controls it, it no longer changes
  useEffect(() => {
    setActiveMenuItem(Math.max(0, menuItem));
  }, [menuItem]);

  const handleQuery = value => setQuery(value, 'pushIn');

  return (
    <Grid>
      <Grid.Column width={5}>
        <SideBar filterType="Contributions" />
      </Grid.Column>
      <Grid.Column width={6}>
        <SearchBar onSearch={handleQuery} searchTerm={query || ''} />
        {query && (
          <>
            <Menu pointing secondary>
              {searchMap.map(([_label, _results], idx) => (
                <SearchTypeMenuItem
                  key={_label}
                  index={idx}
                  active={activeMenuItem === idx}
                  title={Translate.string(_label)}
                  total={_results.total}
                  loading={_results.loading}
                  onClick={handleClick}
                />
              ))}
            </Menu>
            {results.total || isAnyLoading ? (
              <ResultList
                component={Component}
                page={results.page}
                numPages={results.pages}
                data={results.data}
                onPageChange={setPage}
                loading={results.loading}
              />
            ) : (
              <NoResults query={query} />
            )}
          </>
        )}
      </Grid.Column>
      <Grid.Column width={5} />
    </Grid>
  );
}
