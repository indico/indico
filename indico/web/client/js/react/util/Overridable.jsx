// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Overridable, {parametrize, OverridableContext} from 'react-overridable';
import {withRouter} from 'react-router-dom';

export const RouteAwareOverridable = withRouter(Overridable);

export default Overridable;
export {parametrize, OverridableContext};
