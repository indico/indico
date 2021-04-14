// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable */
// XXX: this is loaded from a non-babelized webpack config, so it cannot be an ES module

require('@babel/register');

module.exports = require('./base');
