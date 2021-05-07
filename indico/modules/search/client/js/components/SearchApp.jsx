// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchURL from 'indico-url:search.api_search';
import searchOptionsURL from 'indico-url:search.api_search_options';
import searchPageURL from 'indico-url:search.search';

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState} from 'react';
import {Dropdown, Grid, Loader, Menu, Message} from 'semantic-ui-react';

import {useIndicoAxios, useQueryParams} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {camelizeKeys} from 'indico/utils/case';

import ResultList from './ResultList';
import Attachment from './results/Attachment';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import EventNote from './results/EventNote';
import SearchBar from './SearchBar';
import SideBar from './SideBar';

import './SearchApp.module.scss';

const camelizeValues = obj =>
  Object.entries(obj).reduce(
    (acc, [key, val]) => ({
      ...acc,
      [key]: camelizeKeys(val),
    }),
    {}
  );

function useSearch(url, query, type, categoryId) {
  const [page, setPage] = useState(1);

  const {data, error, loading, lastData} = useIndicoAxios({
    url,
    options: {params: {...query, type, page, category_id: categoryId}},
    forceDispatchEffect: () => query?.q,
    trigger: [url, query, page],
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
        data: camelizeKeys(data?.results || []),
        aggregations: camelizeValues(data?.aggregations || lastData?.aggregations || {}),
        loading: loading || (query.q && !data && !error),
      }),
      [page, data, error, lastData, loading, query.q]
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

function ResultHeader({query, hasResults, categoryTitle}) {
  const isGlobal = !categoryTitle;

  // initial message when no search has been performed
  if (!query && !hasResults) {
    return (
      <Message>
        {isGlobal ? (
          <Translate>Enter a term above to begin searching.</Translate>
        ) : (
          <Translate>
            Enter a term above to begin searching inside the{' '}
            <Param name="categoryTitle" value={categoryTitle} wrapper={<strong />} /> category. You
            can{' '}
            <Param name="link" wrapper={<a href={searchPageURL()} />}>
              search all of Indico instead
            </Param>
            .
          </Translate>
        )}
      </Message>
    );
  }

  // after search, no results
  if (query && !hasResults) {
    return (
      <Message warning={!!query}>
        <Message.Header>
          <Translate>No Results</Translate>
        </Message.Header>
        {isGlobal ? (
          <Translate>
            Your search - <Param name="query" value={query} /> - did not match any results
          </Translate>
        ) : (
          <Translate>
            Your search - <Param name="query" value={query} /> - did not match any results. You
            could try{' '}
            <Param name="link" wrapper={<a href={searchPageURL({q: query})} />}>
              searching all of Indico instead
            </Param>
            .
          </Translate>
        )}
      </Message>
    );
  }

  // after search in a category, offer global search
  if (hasResults && !isGlobal) {
    return (
      <Message>
        Showing results inside{' '}
        <Param name="categoryTitle" value={categoryTitle} wrapper={<strong />} /> category. You can{' '}
        <Param name="link" wrapper={<a href={searchPageURL({q: query})} />}>
          search all of Indico instead
        </Param>
        .
      </Message>
    );
  }

  return null;
}

ResultHeader.propTypes = {
  hasResults: PropTypes.bool,
  query: PropTypes.string,
  categoryTitle: PropTypes.string,
};

ResultHeader.defaultProps = {
  hasResults: false,
  query: undefined,
  categoryTitle: undefined,
};

function SearchOptions({sort, sortOptions, onSortChange}) {
  if (!sortOptions.length) {
    return null;
  }

  const selected = sortOptions.find(x => x.key === sort) || sortOptions[0];

  return (
    <div styleName="search-options">
      <Dropdown
        text={Translate.string('Sort by: {value}', {value: selected.label})}
        onChange={(e, data) => onSortChange(data.value)}
        options={sortOptions.map(x => ({value: x.key, text: x.label}))}
        selectOnNavigation={false}
        selectOnBlur={false}
        value={selected.key}
      />
    </div>
  );
}

SearchOptions.propTypes = {
  sort: PropTypes.string,
  sortOptions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      label: PropTypes.string,
    })
  ),
  onSortChange: PropTypes.func.isRequired,
};

SearchOptions.defaultProps = {
  sort: undefined,
  sortOptions: undefined,
};

export default function SearchApp({category}) {
  const [query, setQuery] = useQueryParams();
  const [activeMenuItem, setActiveMenuItem] = useState(undefined);
  const {q, sort, ...filters} = query;
  const {data: options} = useIndicoAxios({
    url: searchOptionsURL(),
    trigger: 'once',
    camelize: true,
  });
  const [categoryResults, setCategoryPage] = useSearch(
    searchURL(),
    query,
    'category',
    category?.id
  );
  const [eventResults, setEventPage] = useSearch(searchURL(), query, 'event', category?.id);
  const [contributionResults, setContributionPage] = useSearch(
    searchURL(),
    query,
    ['contribution', 'subcontribution'],
    category?.id
  );
  const [fileResults, setFilePage] = useSearch(searchURL(), query, 'attachment', category?.id);
  const [noteResults, setNotePage] = useSearch(searchURL(), query, 'event_note', category?.id);
  const searchMap = [
    [Translate.string('Events'), eventResults, setEventPage, Event],
    [Translate.string('Contributions'), contributionResults, setContributionPage, Contribution],
    [Translate.string('Materials'), fileResults, setFilePage, Attachment],
    [Translate.string('Notes'), noteResults, setNotePage, EventNote],
    [Translate.string('Categories'), categoryResults, setCategoryPage, Category],
  ];
  // Defaults to the first tab loading or with results
  const menuItem =
    activeMenuItem || Math.max(0, searchMap.findIndex(x => x[1].loading || x[1].total));
  const [, results, setPage, Component] = searchMap[menuItem];
  const isAnyLoading = searchMap.some(x => x[1].loading);

  const handleQuery = (value, type = 'q') => setQuery(type, value, type === 'q');

  return (
    <Grid columns={2} doubling padded styleName="grid">
      {Object.keys(results.aggregations).length > 0 && (
        <Grid.Column width={3} only="large screen">
          <SideBar query={filters} aggregations={results.aggregations} onChange={handleQuery} />
        </Grid.Column>
      )}
      <Grid.Column width={7}>
        <SearchBar
          onSearch={handleQuery}
          searchTerm={q || ''}
          placeholders={options?.placeholders || []}
        />
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
        <SearchOptions
          sort={sort}
          sortOptions={options?.sortOptions || []}
          onSortChange={value => handleQuery(value, 'sort')}
        />
        {!isAnyLoading && (
          <ResultHeader query={q} hasResults={!!results.total} categoryTitle={category?.title} />
        )}
        {q && (results.total || isAnyLoading) && (
          <ResultList
            component={Component}
            page={results.page}
            numPages={results.pages}
            data={results.data}
            onPageChange={setPage}
            loading={results.loading}
          />
        )}
      </Grid.Column>
    </Grid>
  );
}

SearchApp.propTypes = {
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
  }),
};

SearchApp.defaultProps = {
  category: null,
};
