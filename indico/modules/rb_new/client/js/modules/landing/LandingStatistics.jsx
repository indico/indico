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
import {Statistic} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';


export default class LandingStatistics extends React.Component {
    render() {
        return (
            <>
                <Statistic size="huge">
                    <Statistic.Value>
                        230
                    </Statistic.Value>
                    <Statistic.Label>
                        <Translate>Active rooms</Translate>
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        70
                    </Statistic.Value>
                    <Statistic.Label>
                        <Translate>Buildings</Translate>
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        25
                    </Statistic.Value>
                    <Statistic.Label>
                        <Translate>Bookings today</Translate>
                    </Statistic.Label>
                </Statistic>
                <Statistic size="huge">
                    <Statistic.Value>
                        20
                    </Statistic.Value>
                    <Statistic.Label>
                        <Translate>Active booking requests</Translate>
                    </Statistic.Label>
                </Statistic>
            </>
        );
    }
}
