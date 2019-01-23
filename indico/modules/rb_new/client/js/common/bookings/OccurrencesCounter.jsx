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
import PropTypes from 'prop-types';
import {Label, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import './OccurrencesCounter.module.scss';


export default function OccurrencesCounter({bookingsCount, newBookingsCount, pastBookingsCount}) {
    return (
        <div styleName="occurrence-count">
            <Popup trigger={<Label color="blue" size="tiny" content={bookingsCount} circular />}
                   position="bottom center"
                   on="hover">
                <Translate>
                    Number of booking occurrences
                </Translate>
            </Popup>
            {newBookingsCount !== null && (
                <div>
                    {pastBookingsCount !== null && (
                        <div styleName="old-occurrences-count">
                            <div styleName="arrow">→</div>
                            <Popup trigger={<Label size="tiny" content={pastBookingsCount} color="orange" circular />}
                                   position="bottom center"
                                   on="hover">
                                <Translate>
                                    Number of past occurrences that will not be modified
                                </Translate>
                            </Popup>
                        </div>
                    )}
                    <div className={toClasses({'new-occurrences-count': true, 'single-arrow': pastBookingsCount === null})}>
                        <div styleName="arrow">→</div>
                        <Popup trigger={<Label size="tiny" content={newBookingsCount} color="green" circular />}
                               position="bottom center"
                               on="hover">
                            <Translate>
                                Number of new occurrences after changes
                            </Translate>
                        </Popup>
                    </div>
                </div>
            )}
        </div>
    );
}

OccurrencesCounter.propTypes = {
    bookingsCount: PropTypes.number.isRequired,
    newBookingsCount: PropTypes.number,
    pastBookingsCount: PropTypes.number,
};

OccurrencesCounter.defaultProps = {
    newBookingsCount: null,
    pastBookingsCount: null,
};
