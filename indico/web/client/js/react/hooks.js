/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import {useEffect} from 'react';


/**
 * Helper to use async functions with useEffect as the function that is
 * passed to useEffect must not return anything except a cleanup function,
 * so passing async functions directly is not allowed.
 *
 * Using this hook, there is obviously no way to return a cleanup function,
 * but this should be used for simple AJAX calls where no cleanup is needed.
 */
export const useAsyncEffect = (fn, ...args) => {
    /* eslint-disable react-hooks/exhaustive-deps */
    useEffect(() => {
        fn();
    }, ...args);
};
