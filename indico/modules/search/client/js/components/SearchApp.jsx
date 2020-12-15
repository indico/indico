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

import React, {useEffect, useReducer, useState} from 'react';
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

  const {data, loading} = useIndicoAxios({
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
    {
      page: data ? data.page : 1,
      pages: data ? data.pages : 1,
      total: data ? data.total : -1,
      data: data ? data.results : [],
      loading,
    },
    setPage,
  ];
}

// eslint-disable-next-line react/prop-types
function SearchTypeMenuItem({name, active, title, total, loading, onClick}) {
  let indicator = null;
  if (loading) {
    indicator = <Loader active inline size="tiny" />;
  } else if (total !== -1) {
    indicator = ` (${total})`;
  }
  return (
    <Menu.Item name={name} active={active} onClick={onClick} disabled={loading || !total}>
      {title}
      {indicator}
    </Menu.Item>
  );
}

export default function SearchApp() {
  const [query, setQuery] = useQueryParam('q', StringParam);
  const [activeMenuItem, setActiveMenuItem] = useState('categories');
  const handleClick = (e, {name}) => {
    setActiveMenuItem(name);
  };

  const [categoryResults, setCategoryPage] = useSearch(searchCategoriesURL(), query);
  const [eventResults, setEventPage] = useSearch(searchEventsURL(), query);
  const [contributionResults, setContributionPage] = useSearch(searchContributionsURL(), query);
  const [fileResults, setFilePage] = useSearch(searchFilesURL(), query);
  const [results, setResults] = useState('initial state');
  const resultMap = {
    categories: categoryResults,
    events: eventResults,
    contributions: contributionResults,
    files: fileResults,
  };
  const resultTypes = ['categories', 'events', 'contributions', 'files'];

  useEffect(() => {
    if (resultMap[activeMenuItem].total !== 0) {
      // don't switch if the currently active type has results
      return;
    }

    const firstTypeWithResults = resultTypes.find(x => resultMap[x].total > 0);
    if (firstTypeWithResults) {
      setActiveMenuItem(firstTypeWithResults);
      return;
    }

    const firstTypeStillSearching = resultTypes.find(x => resultMap[x].loading);
    if (firstTypeStillSearching) {
      setActiveMenuItem(firstTypeStillSearching);
      return;
    }
  }, [
    activeMenuItem,
    categoryResults,
    eventResults,
    contributionResults,
    fileResults,
    resultMap,
    resultTypes,
  ]);

  // handle the correct rendering of NoResults Placeholder
  useEffect(() => {
    if (Object.values(resultMap).some(x => x.total === -1)) {
      setResults('initial state');
      return;
    }
    // if (Object.values(resultMap).some(x => x.loading)) {
    //   setResults('loading');
    //   return;
    // }
    const firstTypeWithResults = resultTypes.find(x => resultMap[x].total !== 0);
    if (firstTypeWithResults) {
      setResults('loaded');
      return;
    }
    setResults('empty');
  }, [resultMap, resultTypes]);

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
              <SearchTypeMenuItem
                name="categories"
                active={activeMenuItem === 'categories' && results !== 'empty'}
                title={Translate.string('Categories')}
                total={categoryResults.total}
                loading={categoryResults.loading}
                onClick={handleClick}
              />
              <SearchTypeMenuItem
                name="events"
                active={activeMenuItem === 'events' && results !== 'empty'}
                title={Translate.string('Events')}
                total={eventResults.total}
                loading={eventResults.loading}
                onClick={handleClick}
              />
              <SearchTypeMenuItem
                name="contributions"
                active={activeMenuItem === 'contributions' && results !== 'empty'}
                title={Translate.string('Contributions')}
                total={contributionResults.total}
                loading={contributionResults.loading}
                onClick={handleClick}
              />
              <SearchTypeMenuItem
                name="files"
                active={activeMenuItem === 'files' && results !== 'empty'}
                title={Translate.string('Materials')}
                total={fileResults.total}
                loading={fileResults.loading}
                onClick={handleClick}
              />
            </Menu>
            {results !== 'empty' ? (
              <>
                {activeMenuItem === 'categories' && (
                  <ResultList
                    component={Category}
                    page={categoryResults.page}
                    numPages={categoryResults.pages}
                    data={categoryResults.data}
                    onPageChange={setCategoryPage}
                    loading={categoryResults.loading}
                  />
                )}
                {activeMenuItem === 'events' && (
                  <ResultList
                    component={Event}
                    page={eventResults.page}
                    numPages={eventResults.pages}
                    data={eventResults.data}
                    onPageChange={setEventPage}
                    loading={eventResults.loading}
                  />
                )}
                {activeMenuItem === 'contributions' && (
                  <ResultList
                    component={Contribution}
                    page={contributionResults.page}
                    numPages={contributionResults.pages}
                    data={contributionResults.data}
                    onPageChange={setContributionPage}
                    loading={contributionResults.loading}
                  />
                )}
                {activeMenuItem === 'files' && (
                  <ResultList
                    component={File}
                    page={fileResults.page}
                    numPages={fileResults.pages}
                    data={fileResults.data}
                    onPageChange={setFilePage}
                    loading={fileResults.loading}
                  />
                )}
              </>
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
