/* This file is part of Indico.
* Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import React from 'react';

import {PluralTranslate, Translate, Singular, Plural, Param} from 'indico/react/i18n';


export default function recurrenceRenderer({type, number, interval}) {
    if (!type) {
        return null;
    }
    if (type === 'single') {
        return <Translate>Once</Translate>;
    } else if (type === 'daily') {
        return <Translate>Daily</Translate>;
    } else if (interval === 'day') {
        return (
            <PluralTranslate count={number}>
                <Singular>
                    Daily
                </Singular>
                <Plural>
                    Every <Param name="number" value={number} /> days
                </Plural>
            </PluralTranslate>
        );
    } else if (interval === 'week') {
        return (
            <PluralTranslate count={number}>
                <Singular>
                    Weekly
                </Singular>
                <Plural>
                    Every <Param name="number" value={number} /> weeks
                </Plural>
            </PluralTranslate>
        );
    } else {
        return (
            <PluralTranslate count={number}>
                <Singular>
                    Monthly
                </Singular>
                <Plural>
                    Every <Param name="number" value={number} /> months
                </Plural>
            </PluralTranslate>
        );
    }
}
