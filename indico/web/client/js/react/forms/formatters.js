// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _slugify from 'slugify';


function trim(value) {
    return value === undefined ? undefined : value.trim();
}


function slugify(value) {
    return value === undefined ? undefined : _slugify(value, {lower: true});
}


export default {
    trim,
    slugify,
};
