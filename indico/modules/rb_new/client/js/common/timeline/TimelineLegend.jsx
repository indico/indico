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

import PropTypes from 'prop-types';
import React from 'react';
import {Label, Segment, List} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {legendLabelShape} from '../../props';

import './TimelineLegend.module.scss';


export default function TimelineLegend({labels, aside, compact}) {
    if (compact) {
        return labels.length ? (
            <List styleName="legend compact">
                {labels.map(({label, style}) => (
                    <List.Item key={label}>
                        <List.Content styleName="labels">
                            <Label styleName={`compact ${style || ''}`} />
                            <span styleName="text">{label}</span>
                        </List.Content>
                    </List.Item>
                ))}
            </List>
        ) : (
            <Translate>No occurrences</Translate>
        );
    } else {
        return (
            <Segment styleName="legend" basic>
                <Label.Group as="span" size="medium" styleName="labels">
                    {labels.map(({label, style}) => (
                        <Label styleName={style || ''} key={label}>{label}</Label>
                    ))}
                </Label.Group>
                {aside}
            </Segment>
        );
    }
}

TimelineLegend.propTypes = {
    labels: PropTypes.arrayOf(legendLabelShape).isRequired,
    aside: PropTypes.node,
    compact: PropTypes.bool
};

TimelineLegend.defaultProps = {
    aside: null,
    compact: false
};
