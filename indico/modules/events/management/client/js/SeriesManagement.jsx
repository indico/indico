// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventSearch from 'indico-url:categories.event_search';
import eventSeriesURL from 'indico-url:event_series.event_series';
import singleEventAPI from 'indico-url:events.single_event_api';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {
  Button,
  Checkbox,
  Confirm,
  Dimmer,
  Divider,
  Dropdown,
  Form,
  Icon,
  List,
  Loader,
  Modal,
  Popup,
} from 'semantic-ui-react';

import {TooltipIfTruncated, IButton} from 'indico/react/components';
import {handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import './SeriesManagement.module.scss';

const debounce = makeAsyncDebounce(250);
const debounceSingle = makeAsyncDebounce(250);

export function SeriesManagement({eventId, categoryId, seriesId, timezone}) {
  const [open, setOpen] = useState(false);
  const [currentEvents, setCurrentEvents] = useState([]);
  const [keyword, setKeyword] = useState(undefined);
  const [results, setResults] = useState([]);
  const [isSearchOpen, setSearchOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [denialReason, setDenialReason] = useState(null);
  const [showSequenceInTitle, setShowSequenceInTitle] = useState(true);
  const [showLinksToOtherEvents, setShowLinksToOtherEvents] = useState(true);
  const localMoment = dt => moment(dt).tz(timezone);
  const hasSeries = seriesId !== null;

  const onClose = () => {
    setOpen(false);
    setKeyword(undefined);
    setCurrentEvents([]);
    setResults([]);
  };

  const onSearchClose = () => {
    setKeyword(undefined);
    setSearchOpen(false);
    setResults([]);
  };

  const getSeriesInfo = async () => {
    let resp;
    try {
      resp = await debounce(() => indicoAxios.get(eventSeriesURL({series_id: seriesId})));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    const data = camelizeKeys(resp.data);
    setCurrentEvents(camelizeKeys(data.events));
    setShowLinksToOtherEvents(data.showLinks);
    setShowSequenceInTitle(data.showSequenceInTitle);
    setLoading(false);
  };

  const getSingleEventInfo = async (evtId, r) => {
    let resp;
    try {
      resp = await debounceSingle(() => indicoAxios.get(singleEventAPI({event_id: evtId})));
      resp = camelizeKeys(resp);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    if (resp.data === null) {
      setDenialReason(Translate.string('No event found with this ID.'));
    } else if (!resp.data.canAccess) {
      setDenialReason(Translate.string("You don't have rights to access this event."));
    } else {
      r([resp.data]);
      setDenialReason(null);
      return;
    }
    r([]);
  };

  const getEventsSearch = async q => {
    let resp;
    try {
      resp = await debounce(() => indicoAxios.get(eventSearch({category_id: categoryId, q})));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setResults(camelizeKeys(resp.data));
    setDenialReason(null);
  };

  const onSearch = async (evt, {searchQuery}) => {
    if (!searchQuery) {
      setResults([]);
      setDenialReason(null);
      return;
    }
    const regexUrl = new RegExp(`^${location.origin.replace('/', '\\/')}\\/event\\/[0-9]+`);
    const match = searchQuery.match(regexUrl);
    if (match) {
      getSingleEventInfo(match[1], setResults);
    } else if (/^#([0-9])+$/.test(searchQuery)) {
      getSingleEventInfo(searchQuery.substr(1), setResults);
    } else {
      getEventsSearch(searchQuery);
    }
    setSearchOpen(true);
  };

  const handleSubmit = () => {
    if (keyword.trim()) {
      onSearch(keyword.trim());
    }
  };

  const eventOptions = results.map(evt => ({
    key: evt.id,
    value: evt.id,
    meta: evt,
    text: evt.title,
    disabled: !evt.canManage || evt.seriesId !== null || !!currentEvents.find(e => e.id === evt.id),
    content: (
      <div styleName="list-flex">
        <span styleName="date-span">{localMoment(evt.startDt).format('ll')}</span>
        <span styleName="event-title">
          {evt.title}
          <br />
          <TooltipIfTruncated>
            <span>
              {evt.categoryChain ? evt.categoryChain.join(' » ') : <Translate>Unlisted</Translate>}
            </span>
          </TooltipIfTruncated>
          {!evt.canManage && (
            <span styleName="warning-reason">
              <br />
              <Translate>You do not have editing rights for this event.</Translate>
            </span>
          )}
          {evt.seriesId !== null && !currentEvents.find(e => e.id === evt.id) && (
            <span styleName="warning-reason">
              <br />
              <Translate>This event is already part of a different series.</Translate>
            </span>
          )}
          {currentEvents.find(e => e.id === evt.id) && (
            <span styleName="positive-note">
              <br />
              <Translate>This event is already part of this series.</Translate>
            </span>
          )}
        </span>
      </div>
    ),
    onClick: (_, e) => {
      if (evt.canManage && evt.seriesId === null && !currentEvents.find(ee => ee.id === evt.id)) {
        setCurrentEvents(
          [...currentEvents, e.meta].sort((a, b) => moment(a.startDt) - moment(b.startDt))
        );
      }
    },
  }));

  const submitSeries = async () => {
    const data = {
      event_ids: currentEvents.map(x => x.id),
      show_sequence_in_title: showSequenceInTitle,
      show_links: showLinksToOtherEvents,
    };
    try {
      if (hasSeries) {
        await indicoAxios.patch(eventSeriesURL({series_id: seriesId}), data);
      } else {
        await indicoAxios.post(eventSeriesURL(), data);
      }
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
  };

  const deleteSeries = async () => {
    try {
      await indicoAxios.delete(eventSeriesURL({series_id: seriesId}));
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
  };

  return (
    <>
      <Confirm
        size="tiny"
        open={confirmOpen}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={deleteSeries}
        content={Translate.string(
          'Do you really want to delete this series? This will NOT delete the events.'
        )}
        header={Translate.string('Delete series?')}
        confirmButton={<Button content={Translate.string('Delete this series')} negative />}
        cancelButton={Translate.string('Cancel')}
      />
      <Modal
        onClose={onClose}
        onOpen={() => {
          setLoading(true);
          setOpen(true);
          if (hasSeries) {
            getSeriesInfo();
          } else {
            getSingleEventInfo(eventId, r => {
              setCurrentEvents(r);
              setLoading(false);
            });
          }
        }}
        open={open}
        trigger={
          hasSeries ? (
            <IButton borderless icon="stack" title={Translate.string('Manage event series')}>
              <Translate>Manage series</Translate>
            </IButton>
          ) : (
            <IButton borderless icon="stack" title={Translate.string('Create event series')}>
              <Translate>Create series</Translate>
            </IButton>
          )
        }
      >
        <Modal.Header>
          <Translate>Manage series</Translate>
        </Modal.Header>
        <Modal.Content>
          <Form onSubmit={handleSubmit}>
            <Dropdown
              fluid
              selection
              search={x => x}
              icon="search"
              selectOnBlur={false}
              selectOnNavigation={false}
              placeholder={Translate.string(
                'Search for an event title or paste an event URL or event ID (#123)'
              )}
              options={eventOptions}
              value={null}
              open={isSearchOpen}
              onSearchChange={onSearch}
              onFocus={() => setSearchOpen(true)}
              onBlur={() => setSearchOpen(false)}
              onClose={onSearchClose}
              noResultsMessage={
                denialReason !== null ? denialReason : Translate.string('No results found.')
              }
              minCharacters={3}
            />
          </Form>
          <Divider horizontal>
            {hasSeries ? (
              <Translate>Events in series</Translate>
            ) : (
              <Translate>Events to add</Translate>
            )}
          </Divider>
          {loading ? (
            <Dimmer active>
              <Loader active />
            </Dimmer>
          ) : (
            <List divided relaxed styleName="evt-list">
              {currentEvents.length > 0 &&
                currentEvents.map(e => (
                  <List.Item key={e.id} styleName="evt-item">
                    <List.Content>
                      <div styleName="list-flex">
                        <span styleName="date-span">
                          {localMoment(e.startDt).format('ll')}
                          <br />
                          {eventId === e.id && (
                            <span styleName="positive-note">
                              (<Translate>this event</Translate>)
                            </span>
                          )}
                        </span>
                        <span styleName="event-title">
                          {e.title}
                          <br />
                          <TooltipIfTruncated>
                            <span styleName="detail">
                              {e.categoryChain ? (
                                e.categoryChain.join(' » ')
                              ) : (
                                <span styleName="warning-reason">
                                  <Translate>Unlisted</Translate>
                                </span>
                              )}
                            </span>
                          </TooltipIfTruncated>
                        </span>
                        {(eventId !== e.id || hasSeries) && (
                          <Popup
                            trigger={
                              <Icon
                                styleName="delete-button"
                                name="close"
                                onClick={() =>
                                  setCurrentEvents(currentEvents.filter(evt => evt.id !== e.id))
                                }
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
          )}
          <Divider horizontal>
            <Translate>Series options</Translate>
          </Divider>
          <Checkbox
            checked={showSequenceInTitle}
            label={Translate.string('Show the sequence number in the event titles')}
            onClick={() => setShowSequenceInTitle(!showSequenceInTitle)}
          />
          <br />
          <Checkbox
            checked={showLinksToOtherEvents}
            label={Translate.string(
              'Show links to the other events of the series on the main event page'
            )}
            onClick={() => setShowLinksToOtherEvents(!showLinksToOtherEvents)}
          />
        </Modal.Content>
        <Modal.Actions>
          {hasSeries && (
            <Button negative onClick={() => setConfirmOpen(true)} floated="left">
              <Translate>Delete series</Translate>
            </Button>
          )}
          <Button
            content={
              hasSeries ? Translate.string('Update series') : Translate.string('Create series')
            }
            onClick={submitSeries}
            color="blue"
            disabled={!currentEvents.length}
          />
          <Button onClick={onClose}>
            <Translate>Cancel</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
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
