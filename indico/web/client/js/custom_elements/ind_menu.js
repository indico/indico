// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import Menu from 'indico/behaviors/menu';
import CustomElementBase from 'indico/custom_elements/_base';

import './ind_menu.scss';

CustomElementBase.defineWhenDomReady('ind-menu', CustomElementBase.fromBehavior(Menu));
