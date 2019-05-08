// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import LogEntryList from '../containers/LogEntryList';
import Toolbar from './Toolbar';


export default function EventLog() {
    return (
        <>
            <Toolbar />
            <LogEntryList />
        </>
    );
}
