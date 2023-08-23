// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {injectModal} from 'indico/react/util';

import PrintReceiptsModal from './printing/PrintReceiptsModal';

import './templates';

window.printReceipts = function({registration_id: registrationIds, event_id: eventId}) {
  injectModal(resolve => (
    <PrintReceiptsModal onClose={resolve} registrationIds={registrationIds} eventId={eventId} />
  ));
};
