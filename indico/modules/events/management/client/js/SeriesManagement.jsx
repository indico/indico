// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventSearch from 'indico-url:categories.event_search';
import eventSeriesURL from 'indico-url:event_series.event_series';
import singleEventAPI from 'indico-url:events.single_event_api';

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Dimmer, Divider, Dropdown, Icon, List, Loader, Popup} from 'semantic-ui-react';

import {TooltipIfTruncated, IButton, RequestConfirmDelete} from 'indico/react/components';
import {FinalCheckbox, FinalField, FinalInput, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm, getChangedValues, getValuesForFields} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import styles from './SeriesManagement.module.scss';

const debounce = makeAsyncDebounce(250);
const debounceSingle = makeAsyncDebounce(250);

export function SeriesManagement({eventId, categoryId, seriesId, timezone}) {
  const hasSeries = seriesId !== null;
  const [open, setOpen] = useState(false);
  const {loading, reFetch, data} = useIndicoAxios(
    hasSeries ? eventSeriesURL({series_id: seriesId}) : singleEventAPI({event_id: eventId}),
    {manual: true}
  );

  const handleOpenClick = async () => {
    await reFetch();
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  // either an actual series or a new series-like object containing the initial event
  const series = data
    ? hasSeries
      ? data
      : {
          id: null,
          events: [data],
          show_sequence_in_title: false,
          show_links: false,
          event_title_pattern: '',
        }
    : null;

  return (
    <>
      {hasSeries ? (
        <IButton
          borderless
          icon="stack"
          title={Translate.string('Manage event series')}
          onClick={handleOpenClick}
        >
          <Translate>Manage series</Translate>
        </IButton>
      ) : (
        <IButton
          borderless
          icon="stack"
          title={Translate.string('Create event series')}
          onClick={handleOpenClick}
        >
          <Translate>Create series</Translate>
        </IButton>
      )}
      <Dimmer active={loading} page inverted>
        <Loader />
      </Dimmer>
      {open && (
        <SeriesManagementModal
          currentEventId={eventId}
          categoryId={categoryId}
          timezone={timezone}
          series={series}
          onClose={handleClose}
        />
      )}
    </>
  );
}

SeriesManagement.propTypes = {
  eventId: PropTypes.number.isRequired,
  categoryId: PropTypes.number.isRequired,
  timezone: PropTypes.string.isRequired,
  seriesId: PropTypes.number,
};

SeriesManagement.defaultProps = {
  seriesId: null,
};

function SeriesManagementModal({currentEventId, categoryId, series, timezone, onClose}) {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

  const existingSeries = series.id !== null;
  const localMoment = dt => moment(dt).tz(timezone);

  const handleSubmit = async (data, form) => {
    const payload = existingSeries ? getChangedValues(data, form) : getValuesForFields(data, form);
    if (payload.events) {
      payload.event_ids = payload.events.map(e => e.id);
      delete payload.events;
    }

    try {
      if (existingSeries) {
        await indicoAxios.patch(eventSeriesURL({series_id: series.id}), payload);
      } else {
        await indicoAxios.post(eventSeriesURL(), payload);
      }
    } catch (e) {
      return handleSubmitError(e, {event_ids: 'events'});
    }

    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const deleteSeries = async () => {
    try {
      await indicoAxios.delete(eventSeriesURL({series_id: series.id}));
    } catch (e) {
      handleAxiosError(e);
      return true;
    }
    location.reload();
  };

  return (
    <>
      <FinalModalForm
        id="event-series"
        header={
          existingSeries ? Translate.string('Manage series') : Translate.string('Create series')
        }
        size="standard"
        alignTop
        onSubmit={handleSubmit}
        onClose={onClose}
        initialValues={series}
        disabledUntilChange={existingSeries}
        extraActions={fprops =>
          existingSeries && (
            <Button
              style={{marginRight: 'auto'}}
              onClick={() => setDeleteConfirmOpen(true)}
              disabled={fprops.submitting}
              negative
            >
              <Translate>Delete series</Translate>
            </Button>
          )
        }
        submitLabel={
          existingSeries ? Translate.string('Update series') : Translate.string('Create series')
        }
      >
        {() => (
          <>
            <FinalField
              name="events"
              isEqual={(a, b) => _.isEqual((a || []).map(e => e.id), (b || []).map(e => e.id))}
              validate={val => {
                if (!val.length) {
                  return Translate.string('A series needs to contain at least one event.');
                }
              }}
              component={SeriesEvents}
              localMoment={localMoment}
              categoryId={categoryId}
              currentEventId={currentEventId}
              existingSeriesId={series.id}
              divider={
                <Divider horizontal>
                  {existingSeries ? (
                    <Translate>Events in series</Translate>
                  ) : (
                    <Translate>Events to add</Translate>
                  )}
                </Divider>
              }
            />
            <Divider horizontal>
              <Translate>Series options</Translate>
            </Divider>
            <FinalCheckbox
              name="show_sequence_in_title"
              label={Translate.string(
                'Show the sequence number in the event titles (lectures only)'
              )}
            />
            <FinalCheckbox
              name="show_links"
              label={Translate.string(
                'Show links to the other events of the series on the main event page'
              )}
            />
            <FinalInput
              name="event_title_pattern"
              label={Translate.string('Event title pattern')}
              description={
                <Translate>
                  Title pattern for cloned events. Must contain the{' '}
                  <Param name="placeholder" wrapper={<code />} value="{n}" /> placeholder which will
                  indicate the new event's position in the series.
                </Translate>
              }
              validate={val => {
                if (val && !val.includes('{n}')) {
                  return Translate.string(
                    'Title pattern must contain the {placeholder} placeholder',
                    {placeholder: '{n}'}
                  );
                }
              }}
            />
          </>
        )}
      </FinalModalForm>
      <RequestConfirmDelete
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        requestFunc={deleteSeries}
        persistent
      >
        <Translate>
          Do you really want to delete this series? The associated events will not be deleted.
        </Translate>
      </RequestConfirmDelete>
    </>
  );
}

SeriesManagementModal.propTypes = {
  currentEventId: PropTypes.number.isRequired,
  categoryId: PropTypes.number.isRequired,
  series: PropTypes.shape({
    id: PropTypes.number,
    events: PropTypes.arrayOf(PropTypes.object).isRequired,
    show_sequence_in_title: PropTypes.bool.isRequired,
    show_links: PropTypes.bool.isRequired,
    event_title_pattern: PropTypes.string.isRequired,
  }).isRequired,
  timezone: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

function SeriesEvents({
  value: currentEvents,
  onChange,
  onFocus,
  onBlur,
  divider,
  localMoment,
  categoryId,
  currentEventId,
  existingSeriesId,
}) {
  const [searchQuery, setSearchQuery] = useState(undefined);
  const [results, setResults] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [isSearching, setSearching] = useState(false);
  const [denialReason, setDenialReason] = useState(null);

  const existingSeries = existingSeriesId !== null;

  const setTouched = () => {
    // pretend focus+blur to mark the field as touched even if the dropdown was never focused
    onFocus();
    onBlur();
  };

  const getSingleEventInfo = async eventId => {
    let resp;
    try {
      resp = await debounceSingle(() => indicoAxios.get(singleEventAPI({event_id: +eventId})));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (resp.data === null) {
      setDenialReason(Translate.string('No event found with this ID.'));
    } else if (!resp.data.can_access) {
      setDenialReason(Translate.string("You don't have rights to access this event."));
    } else if (!resp.data.category_chain) {
      setDenialReason(Translate.string('This event is unlisted.'));
    } else {
      setResults([resp.data]);
      setDenialReason(null);
      setSearching(false);
      return;
    }
    setSearching(false);
    setResults([]);
  };

  const searchEvents = async (q, searchOffset = 0, addToResults = false) => {
    let resp;
    try {
      resp = await debounce(() =>
        indicoAxios.get(eventSearch({category_id: categoryId, q, offset: searchOffset}))
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (addToResults) {
      setResults([...results, ...resp.data.events]);
    } else {
      setResults(resp.data.events);
    }
    setHasMore(resp.data.has_more);
    setDenialReason(null);
    setSearching(false);
  };

  const handleSearch = async (__, {searchQuery: query}) => {
    setHasMore(false);
    setSearchQuery(query);
    query = query.trim();
    setDenialReason(null);
    if (!query) {
      setSearching(false);
      setResults([]);
      return;
    }
    const regexUrl = new RegExp(`^${location.origin.replace('/', '\\/')}\\/event\\/([0-9]+)`);
    const match = query.match(regexUrl);
    if (match) {
      setSearching(true);
      getSingleEventInfo(match[1], setResults);
    } else if (/^#([0-9])+$/.test(query)) {
      setSearching(true);
      getSingleEventInfo(query.substr(1), setResults);
    } else if (query !== '#') {
      setSearching(true);
      searchEvents(query);
    }
  };

  const currentEventIdsSet = new Set(currentEvents.map(e => e.id));

  let eventOptions = results.map(evt => ({
    key: evt.id,
    value: evt.id,
    text: evt.title,
    disabled:
      !evt.can_manage ||
      !evt.category_chain ||
      (evt.series_id !== existingSeriesId && evt.series_id !== null) ||
      currentEventIdsSet.has(evt.id),
    content: (
      <div styleName="list-flex">
        <span styleName="date-span">{localMoment(evt.start_dt).format('ll')}</span>
        <span styleName="event-title">
          {evt.title}
          <br />
          <TooltipIfTruncated>
            <span styleName="category-chain">
              {evt.category_chain ? (
                evt.category_chain.join(' » ')
              ) : (
                <Translate>Unlisted</Translate>
              )}
            </span>
          </TooltipIfTruncated>
          {!evt.can_manage && (
            <span styleName="warning-reason">
              <br />
              <Translate>You do not have editing rights for this event.</Translate>
            </span>
          )}
          {!evt.category_chain && (
            <span styleName="warning-reason">
              <br />
              <Translate>This event is unlisted.</Translate>
            </span>
          )}
          {evt.series_id !== existingSeriesId && evt.series_id !== null && (
            <span styleName="warning-reason">
              <br />
              <Translate>This event is already part of a different series.</Translate>
            </span>
          )}
          {currentEventIdsSet.has(evt.id) && (
            <span styleName="positive-note">
              <br />
              <Translate>This event is already part of this series.</Translate>
            </span>
          )}
        </span>
      </div>
    ),
  }));

  const loadMore = () => {
    setSearching(true);
    searchEvents(searchQuery.trim(), results.length, true);
  };

  if (eventOptions.length > 0 && hasMore) {
    eventOptions = [
      ...eventOptions,
      {
        key: '_',
        value: '_',
        className: styles['load-more'],
        content: (
          <div
            onClick={e => {
              // The dropdown item with the 'Load more' button should not be selectable.
              // This prevents triggering onChange on the dropdown when the item is clicked.
              e.stopPropagation();
            }}
          >
            <Button
              primary
              compact
              size="small"
              type="button"
              loading={isSearching}
              onClick={loadMore}
            >
              <Translate>Load more</Translate>
            </Button>
          </div>
        ),
      },
    ];
  }

  return (
    <>
      <Dropdown
        fluid
        selection
        search={x => x}
        icon="search"
        closeOnChange={false}
        selectOnBlur={false}
        selectOnNavigation={false}
        placeholder={Translate.string(
          'Search for an event title or paste an event URL or event ID (#123)'
        )}
        options={eventOptions}
        value={null}
        loading={isSearching}
        onSearchChange={handleSearch}
        searchQuery={searchQuery}
        onChange={(__, {value}) => {
          if (value === '_') {
            return;
          }
          const event = results.find(e => e.id === value);
          const newEvents = [...currentEvents, event].sort(
            (a, b) => moment(a.start_dt) - moment(b.start_dt)
          );
          onChange(newEvents);
        }}
        onFocus={onFocus}
        onBlur={onBlur}
        noResultsMessage={
          isSearching
            ? Translate.string('Searching...')
            : denialReason !== null
            ? denialReason
            : searchQuery
            ? Translate.string('No results found.')
            : Translate.string('Enter search term')
        }
      />
      {divider}
      <List divided relaxed styleName="evt-list">
        {currentEvents.map(event => (
          <List.Item key={event.id} styleName="evt-item">
            <List.Content>
              <div styleName="list-flex">
                <span styleName="date-span">
                  {localMoment(event.start_dt).format('ll')}
                  <br />
                  {currentEventId === event.id && (
                    <span styleName="positive-note">
                      (<Translate>this event</Translate>)
                    </span>
                  )}
                </span>
                <span styleName="event-title">
                  {event.title}
                  <br />
                  <TooltipIfTruncated>
                    <span styleName="detail">
                      {event.category_chain ? (
                        event.category_chain.join(' » ')
                      ) : (
                        <span styleName="warning-reason">
                          <Translate>Unlisted</Translate>
                        </span>
                      )}
                    </span>
                  </TooltipIfTruncated>
                </span>
                {(currentEventId !== event.id || existingSeries) && (
                  <Popup
                    trigger={
                      <Icon
                        styleName="delete-button"
                        name="close"
                        onClick={() => {
                          setTouched();
                          onChange(currentEvents.filter(e => e.id !== event.id));
                        }}
                        link
                      />
                    }
                    content={Translate.string('Remove from event series')}
                    position="bottom center"
                  />
                )}
              </div>
            </List.Content>
          </List.Item>
        ))}
      </List>
    </>
  );
}

SeriesEvents.propTypes = {
  value: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
  divider: PropTypes.node.isRequired,
  localMoment: PropTypes.func.isRequired,
  categoryId: PropTypes.number.isRequired,
  currentEventId: PropTypes.number.isRequired,
  existingSeriesId: PropTypes.number,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
};

SeriesEvents.defaultProps = {
  existingSeriesId: null,
};
