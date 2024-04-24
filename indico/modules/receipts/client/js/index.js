// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {injectModal} from 'indico/react/util';

import PrintReceiptsModal from './printing/PrintReceiptsModal';

window.printReceipts = function({
  registration_id: registrationIds,
  event_id: eventId,
  reload_after: reloadAfter,
}) {
  injectModal(resolve => (
    <PrintReceiptsModal
      onClose={generated => {
        if (generated && reloadAfter) {
          location.reload();
        } else {
          resolve();
        }
      }}
      registrationIds={registrationIds}
      eventId={eventId}
    />
  ));
};
