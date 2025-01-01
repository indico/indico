// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventRequestsURL from 'indico-url:categories.api_event_move_requests';
import eventURL from 'indico-url:events.display';

import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Button, Checkbox, Image, Input, Placeholder, Table} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import './CategoryModeration.module.scss';

function getEventTime({startDt, endDt}) {
  startDt = moment(startDt);
  endDt = moment(endDt);

  if (startDt.isSame(endDt, 'day')) {
    return `${startDt.format('L LT')} → ${endDt.format('LT')}`;
  } else {
    return `${startDt.format('L LT')} → ${endDt.format('L LT')}`;
  }
}

function PlaceholderTableRow() {
  return (
    <Table.Row>
      <Table.Cell collapsing>
        <Checkbox />
      </Table.Cell>
      <Table.Cell colSpan="5">
        <Placeholder fluid>
          <Placeholder.Header image>
            <Placeholder.Line />
            <Placeholder.Line />
          </Placeholder.Header>
        </Placeholder>
      </Table.Cell>
    </Table.Row>
  );
}

function MoveRequest({
  requestor,
  event,
  category,
  requestorComment,
  requestedDt,
  selected,
  onSelect,
}) {
  const {fullName, avatarURL, affiliation} = requestor;
  return (
    <>
      <Table.Row>
        <Table.Cell collapsing>
          <Checkbox checked={selected} onChange={onSelect} />
        </Table.Cell>
        <Table.Cell styleName="user">
          <Image styleName="avatar" src={avatarURL} size="mini" avatar />
          <span>
            {fullName} {affiliation && `(${affiliation})`}
          </span>
        </Table.Cell>
        <Table.Cell>
          <a href={eventURL({event_id: event.id})}>{event.title}</a>
        </Table.Cell>
        {category ? (
          <Table.Cell>{category.chainTitles.join(' » ')}</Table.Cell>
        ) : (
          <Translate as={Table.Cell}>Unlisted event</Translate>
        )}
        <Table.Cell>{getEventTime(event)}</Table.Cell>
        <Table.Cell>
          <span title={moment(requestedDt).format('L LT')}>{moment(requestedDt).fromNow()}</span>
        </Table.Cell>
      </Table.Row>
      {requestorComment ? (
        <Table.Row>
          <Table.Cell styleName="no-border" />
          <Table.Cell colSpan="5" styleName="no-border">
            {requestorComment}
          </Table.Cell>
        </Table.Row>
      ) : null}
    </>
  );
}

MoveRequest.propTypes = {
  requestor: PropTypes.shape({
    fullName: PropTypes.string,
    avatarURL: PropTypes.string,
    affiliation: PropTypes.string,
  }).isRequired,
  event: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    startDt: PropTypes.string.isRequired,
    endDt: PropTypes.string.isRequired,
  }).isRequired,
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    chainTitles: PropTypes.arrayOf(PropTypes.string).isRequired,
  }),
  requestedDt: PropTypes.string.isRequired,
  requestorComment: PropTypes.string.isRequired,
  selected: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};

MoveRequest.defaultProps = {
  selected: false,
  category: null,
};

function RequestList({requests, onSubmit, loading}) {
  const [selected, _setSelected] = useState(new Set());
  const [reason, setReason] = useState('');
  const isAnySelected = selected.size > 0;

  const submit = accept => {
    _setSelected(new Set());
    onSubmit(Array.from(selected), accept, reason);
  };

  const select = id =>
    _setSelected(state => {
      const set = new Set([...state, id]);
      if (state.has(id)) {
        set.delete(id);
      }
      return set;
    });

  if (requests.length === 0 && !loading) {
    return <Translate as="p">There are no event move requests.</Translate>;
  }

  return (
    <Table styleName="table">
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell />
          <Translate as={Table.HeaderCell}>User</Translate>
          <Translate as={Table.HeaderCell}>Event</Translate>
          <Translate as={Table.HeaderCell}>Category</Translate>
          <Translate as={Table.HeaderCell}>Event Date</Translate>
          <Translate as={Table.HeaderCell}>Requested Date</Translate>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {loading ? (
          <PlaceholderTableRow />
        ) : (
          requests.map(({id, requestor, requestorComment, event, category, requestedDt}) => (
            <MoveRequest
              key={id}
              id={id}
              event={event}
              category={category}
              requestor={requestor}
              requestedDt={requestedDt}
              requestorComment={requestorComment}
              selected={selected.has(id)}
              onSelect={() => select(id)}
            />
          ))
        )}
      </Table.Body>
      <Table.Footer fullWidth>
        <Table.Row>
          <Table.HeaderCell />
          <Table.HeaderCell colSpan="5">
            <div styleName={`table-footer ${!isAnySelected ? 'disabled' : ''}`}>
              <Translate as={Button} onClick={() => submit(true)} color="teal">
                Approve
              </Translate>
              <Translate as="span" styleName="text-separator">
                or
              </Translate>
              <Input
                size="small"
                placeholder={Translate.string('Provide the rejection reason')}
                value={reason}
                onChange={(_, {value}) => setReason(value)}
              />
              <Translate as="span" styleName="text-separator">
                and
              </Translate>
              <Translate as={Button} onClick={() => submit(false, reason)} color="red">
                Reject
              </Translate>
            </div>
          </Table.HeaderCell>
        </Table.Row>
      </Table.Footer>
    </Table>
  );
}

RequestList.propTypes = {
  requests: PropTypes.array.isRequired,
  onSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool,
};

RequestList.defaultProps = {
  loading: false,
};

export default function CategoryModeration({categoryId}) {
  const {data, lastData, loading, reFetch} = useIndicoAxios(
    {url: eventRequestsURL({category_id: categoryId})},
    {camelize: true}
  );

  const setRequestsState = async (requests, accept, reason) => {
    const url = eventRequestsURL({category_id: categoryId});
    try {
      await indicoAxios.post(url, {requests, accept, reason});
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const numRequests = data?.length;
  useEffect(() => {
    const badge = document.querySelector(
      '#side-menu-category-management-sidemenu .item.active .badge'
    );

    if (!badge || numRequests === undefined) {
      return;
    }

    if (numRequests) {
      badge.textContent = numRequests;
    } else {
      badge.style.display = 'none';
    }
  }, [numRequests]);

  if (!lastData) {
    return null;
  }

  return (
    <RequestList requests={data || []} onSubmit={setRequestsState} loading={!data || loading} />
  );
}

CategoryModeration.propTypes = {
  categoryId: PropTypes.number.isRequired,
};
