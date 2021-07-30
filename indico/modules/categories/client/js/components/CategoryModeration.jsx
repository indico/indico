// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventRequestsURL from 'indico-url:categories.api_event_move_requests';
import eventURL from 'indico-url:events.display';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Checkbox, Dropdown, Image, Input, Placeholder, Table} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {serializeDate} from 'indico/utils/date';
import './CategoryModeration.module.scss';

/* eslint-disable react/jsx-no-useless-fragment */

function PlaceholderTableRow() {
  return (
    <Table.Row>
      <Table.Cell collapsing>
        <Checkbox />
      </Table.Cell>
      <Table.Cell colSpan="4">
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

function RequestTableRow({submitter, event, submittedDt, selected, onSelect}) {
  const {fullName, avatarURL, affiliation} = submitter;
  return (
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
      <Table.Cell>{serializeDate(submittedDt)}</Table.Cell>
    </Table.Row>
  );
}

RequestTableRow.propTypes = {
  submitter: PropTypes.shape({
    fullName: PropTypes.string,
    avatarURL: PropTypes.string,
    affiliation: PropTypes.string,
  }).isRequired,
  event: PropTypes.shape({
    id: PropTypes.number,
    title: PropTypes.string,
  }).isRequired,
  submittedDt: PropTypes.string.isRequired,
  selected: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
};

RequestTableRow.defaultProps = {
  selected: false,
};

const judgmentOptions = [
  {icon: 'checkmark', text: Translate.string('Approve'), value: true},
  {icon: 'close', text: Translate.string('Reject'), value: false},
];

function RequestList({requests, onSubmit, loading}) {
  const [selected, _setSelected] = useState(new Set());
  const [judgeValue, setJudgeValue] = useState(judgmentOptions[0].value);
  const [reason, setReason] = useState(undefined);
  const isAnySelected = selected.size > 0;
  const judgeOption = judgmentOptions.find(x => x.value === judgeValue);

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
    <Table celled>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell />
          <Translate as={Table.HeaderCell}>User</Translate>
          <Translate as={Table.HeaderCell}>Event</Translate>
          <Translate as={Table.HeaderCell}>Submitted Date</Translate>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {loading ? (
          <PlaceholderTableRow />
        ) : (
          requests.map(({id, submitter, event, submittedDt}) => (
            <RequestTableRow
              key={id}
              id={id}
              event={event}
              submitter={submitter}
              submittedDt={submittedDt}
              selected={selected.has(id)}
              onSelect={() => select(id)}
            />
          ))
        )}
      </Table.Body>
      <Table.Footer fullWidth>
        <Table.Row>
          <Table.HeaderCell />
          <Table.HeaderCell colSpan="4">
            <div styleName={`table-footer ${!isAnySelected ? 'disabled' : ''}`}>
              <Button.Group className="small" color={judgeValue ? 'teal' : 'red'}>
                <Button onClick={() => submit(judgeValue)}>{judgeOption.text}</Button>
                <Dropdown
                  className="button icon small"
                  floating
                  value={judgeValue}
                  options={judgmentOptions}
                  trigger={<></>}
                  onChange={(_, {value}) => setJudgeValue(value)}
                />
              </Button.Group>
              {!judgeValue && (
                <>
                  <Translate as="span" styleName="text-separator">
                    and
                  </Translate>
                  <Input
                    size="small"
                    placeholder={Translate.string('Provide the rejection reason')}
                    value={reason}
                    onChange={(_, {value}) => setReason(value)}
                  />
                </>
              )}
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
  const {data, loading, reFetch} = useIndicoAxios({
    url: eventRequestsURL({category_id: categoryId}),
    trigger: categoryId,
    camelize: true,
  });

  const setRequestsState = async (requests, accept, reason) => {
    const url = eventRequestsURL({category_id: categoryId});
    try {
      await indicoAxios.post(url, {requests, accept, reason});
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  return (
    <RequestList requests={data || []} onSubmit={setRequestsState} loading={!data || loading} />
  );
}

CategoryModeration.propTypes = {
  categoryId: PropTypes.number.isRequired,
};
