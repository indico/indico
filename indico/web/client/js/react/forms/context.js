// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

// This context should have the form of `['FormIdentifier', 'fieldIdentifier]` and it can be used
// in places where a react component inside such a form defines plugin entry points and plugins
// using those entry points need to determine where the component is actually used (ie if it's
// the correct form).
// XXX: Consider this unstable. It may be worth splitting this into separate contexts for the
// form and the field at later point, especially in case we want to use this for all forms, including
// purely react-based ones (there it would make much more sense to define the form context once,
// and then the field context on the field component). But for now it works fine as-is.
const FormContext = React.createContext(null);
export default FormContext;
