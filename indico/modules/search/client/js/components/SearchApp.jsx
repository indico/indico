// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchCategoriesURL from 'indico-url:search.search_categories';
import searchEventsURL from 'indico-url:search.search_events';
import searchContributionsURL from 'indico-url:search.search_contributions';
import searchFilesURL from 'indico-url:search.search_files';

import React, {useEffect, useReducer, useState} from 'react';
import {Loader, Menu} from 'semantic-ui-react';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import ResultList from './ResultList';
import SearchBar from './SearchBar';
import Category from './results/Category';
import Event from './results/Event';
import Contribution from './results/Contribution';
import File from './results/File';
import NoResults from './results/NoResults';

import './SearchApp.module.scss';

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
    forceDispatchEffect: () => !!query.length,
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
    indicator = <Loader active inline size="tiny" style={{marginLeft: '5px'}} />;
  } else if (total) {
    indicator = ` (${total})`;
  }
  return (
    <Menu.Item name={name} active={active} onClick={onClick} disabled={loading || !total}>
      {title}
      {indicator}
    </Menu.Item>
  );
}

function handleURLchange(q, setQ, setQuery) {
  if (window.location.search.slice(1) !== q) {
    setQ(window.location.search.slice(1));
    setQuery(window.location.search.slice(3));
  }
}

export default function SearchApp() {
  const [query, setQuery] = useState('');
  const [q, setQ] = useState('');
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
    if (Object.values(resultMap).some(x => x.loading) || resultMap[activeMenuItem].total !== 0) {
      // don't switch while loading or if the currently active type has results
      return;
    }
    const firstTypeWithResults = resultTypes.find(x => resultMap[x].total !== 0);
    if (firstTypeWithResults) {
      setActiveMenuItem(firstTypeWithResults);
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
    if (Object.values(resultMap).some(x => x.loading)) {
      setResults('loading');
      return;
    }
    const firstTypeWithResults = resultTypes.find(x => resultMap[x].total !== 0);
    if (firstTypeWithResults) {
      setResults('loaded');
      return;
    }
    setResults('empty');
  }, [resultMap, resultTypes]);

  handleURLchange(q, setQ, setQuery);

  return (
    <div>
      <SearchBar onSearch={setQuery} />
      {/* if there's a query submitted and at least one resultsType has some results render the tabs */}
      {/* still not working very well, needs a bit of fine tuning here */}
      {!!query && (
        <>
          {results === 'loaded' && (
            <>
              <Menu pointing secondary>
                <SearchTypeMenuItem
                  name="categories"
                  active={activeMenuItem === 'categories'}
                  title={Translate.string('Categories')}
                  total={categoryResults.total}
                  loading={categoryResults.loading}
                  onClick={handleClick}
                />
                <SearchTypeMenuItem
                  name="events"
                  active={activeMenuItem === 'events'}
                  title={Translate.string('Events')}
                  total={eventResults.total}
                  loading={eventResults.loading}
                  onClick={handleClick}
                />
                <SearchTypeMenuItem
                  name="contributions"
                  active={activeMenuItem === 'contributions'}
                  title={Translate.string('Contributions')}
                  total={contributionResults.total}
                  loading={contributionResults.loading}
                  onClick={handleClick}
                />
                <SearchTypeMenuItem
                  name="files"
                  active={activeMenuItem === 'files'}
                  title={Translate.string('Materials')}
                  total={fileResults.total}
                  loading={fileResults.loading}
                  onClick={handleClick}
                />
              </Menu>

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
          )}
          {results === 'empty' && <NoResults query={query} />}
        </>
      )}
    </div>
  );
}
