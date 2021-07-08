import eventRequestsURL from 'indico-url:categories.api_event_move_requests';
import eventURL from 'indico-url:events.display';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Checkbox, Image, Table} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {serializeDate} from 'indico/utils/date';
import './CategoryModeration.module.scss';

function EventRequestList({requests, onApprove, onReject}) {
  const [selected, _setSelected] = useState(new Set());
  const isAnySelected = selected.size > 0;

  const submit = event => {
    _setSelected(new Set());
    event(Array.from(selected));
  };

  const select = id =>
    _setSelected(state => {
      const set = new Set([...state, id]);
      if (state.has(id)) {
        set.delete(id);
      }
      return set;
    });

  if (requests.length === 0) {
    return <Translate as="p">There are no event move requests</Translate>;
  }

  return (
    <>
      {/* TODO: check if module is enabled */}
      <Table celled>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell />
            <Table.HeaderCell>User</Table.HeaderCell>
            <Table.HeaderCell>Event</Table.HeaderCell>
            <Table.HeaderCell>State</Table.HeaderCell>
            <Table.HeaderCell>Submitted Date</Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {requests.map(({id, submitter, event, state, submittedDt}) => (
            <Table.Row key={id}>
              <Table.Cell collapsing>
                <Checkbox
                  checked={selected.has(id)}
                  onChange={() => select(id)}
                  disabled={state !== 'pending'}
                />
              </Table.Cell>
              <Table.Cell styleName="user">
                <Image styleName="avatar" src={submitter.avatarURL} size="mini" avatar />
                {submitter.name} {submitter.affiliation && `(${submitter.affiliation})`}
              </Table.Cell>
              <Table.Cell>
                <a href={eventURL({event_id: event.id})}>{event.title}</a>
              </Table.Cell>
              <Table.Cell>{state}</Table.Cell>
              <Table.Cell>{serializeDate(submittedDt)}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
        <Table.Footer fullWidth>
          <Table.Row>
            <Table.HeaderCell />
            <Table.HeaderCell colSpan="4">
              <Button size="small" onClick={() => submit(onApprove)} disabled={!isAnySelected}>
                Approve
              </Button>
              <Button size="small" onClick={() => submit(onReject)} disabled={!isAnySelected}>
                Reject
              </Button>
            </Table.HeaderCell>
          </Table.Row>
        </Table.Footer>
      </Table>
    </>
  );
}

EventRequestList.propTypes = {
  requests: PropTypes.array.isRequired,
  onApprove: PropTypes.func.isRequired,
  onReject: PropTypes.func.isRequired,
};

export default function CategoryModeration({categoryId}) {
  const {data, reFetch} = useIndicoAxios({
    url: eventRequestsURL({category_id: categoryId}),
    trigger: categoryId,
    camelize: true,
  });

  const setRequestsState = async (requests, state) => {
    const url = eventRequestsURL({category_id: categoryId});
    try {
      await indicoAxios.post(url, {requests, state});
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  return (
    <EventRequestList
      requests={data || []}
      onApprove={ids => setRequestsState(ids, 'accepted')}
      onReject={ids => setRequestsState(ids, 'rejected')}
    />
  );
}

CategoryModeration.propTypes = {
  categoryId: PropTypes.number.isRequired,
};
