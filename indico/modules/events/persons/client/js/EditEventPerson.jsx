// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import updatePersonURL from 'indico-url:persons.update_person';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';

import {PersonDetailsModal} from 'indico/react/components';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

function EditEventPerson({
  eventId,
  person,
  hasPredefinedAffiliations,
  allowCustomAffiliations,
  replacePersonRow,
}) {
  const [modalOpen, setModalOpen] = useState(false);

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    if (!hasPredefinedAffiliations) {
      // changedValues.affiliation is already there and used
      delete changedValues.affiliationData;
    } else if (changedValues.affiliationData) {
      changedValues.affiliation = changedValues.affiliationData.text.trim();
      changedValues.affiliationId = changedValues.affiliationData.id;
      delete changedValues.affiliationData;
    }
    let resp;
    try {
      resp = await indicoAxios.patch(
        updatePersonURL({event_id: eventId, person_id: person.id}),
        snakifyKeys(changedValues)
      );
    } catch (e) {
      return handleSubmitError(e, {affiliation_data: 'affiliationData'});
    }

    replacePersonRow(resp.data.html);
    await new Promise(() => {});
  };

  return (
    <>
      <a
        className="i-link icon-edit"
        title={Translate.string('Edit person information')}
        onClick={() => setModalOpen(true)}
      />
      {modalOpen && (
        <PersonDetailsModal
          person={person}
          hasPredefinedAffiliations={hasPredefinedAffiliations}
          allowCustomAffiliations={allowCustomAffiliations}
          hideEmailField
          onClose={() => setModalOpen(false)}
          onSubmit={handleSubmit}
        />
      )}
    </>
  );
}

EditEventPerson.propTypes = {
  eventId: PropTypes.number.isRequired,
  person: PropTypes.object.isRequired,
  hasPredefinedAffiliations: PropTypes.bool.isRequired,
  allowCustomAffiliations: PropTypes.bool.isRequired,
  replacePersonRow: PropTypes.func.isRequired,
};

window.setupEditEventPerson = (
  eventId,
  person,
  hasPredefinedAffiliations,
  allowCustomAffiliations
) => {
  const container = document.querySelector(`#edit-person-${person.id}`);
  const replacePersonRow = html => {
    ReactDOM.unmountComponentAtNode(container);
    // sorry for using jquery here, but it's the most convenient way to execute inline JS..
    $(`#person-${person.id}`).html(html);
  };

  ReactDOM.render(
    <EditEventPerson
      eventId={eventId}
      person={camelizeKeys(person)}
      hasPredefinedAffiliations={hasPredefinedAffiliations}
      allowCustomAffiliations={allowCustomAffiliations}
      replacePersonRow={replacePersonRow}
    />,
    container
  );
};
