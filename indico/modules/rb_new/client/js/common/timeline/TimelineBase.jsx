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

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import DailyTimelineContent from './DailyTimelineContent';
import TimelineItem from './TimelineItem';

import './Timeline.module.scss';


export default class TimelineBase extends React.Component {
    static propTypes = {
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        emptyMessage: PropTypes.node,
        extraContent: PropTypes.node,
        minHour: PropTypes.number.isRequired,
        maxHour: PropTypes.number.isRequired,
        step: PropTypes.number,
        onClick: PropTypes.func,
        isLoading: PropTypes.bool,
        recurrenceType: PropTypes.string,
        itemClass: PropTypes.func,
        itemProps: PropTypes.object,
        longLabel: PropTypes.bool,
        onClickLabel: PropTypes.func,
        lazyScroll: PropTypes.object
    };

    static defaultProps = {
        emptyMessage: (
            <Message warning>
                <Translate>
                    No occurrences found
                </Translate>
            </Message>
        ),
        step: 2,
        onClick: null,
        extraContent: null,
        isLoading: false,
        recurrenceType: 'single',
        itemClass: TimelineItem,
        itemProps: {},
        longLabel: false,
        onClickLabel: null,
        lazyScroll: null
    };

    renderTimeline = () => {
        const {
            extraContent, maxHour, minHour, onClick, recurrenceType, rows, step, isLoading, itemClass,
            itemProps, longLabel, onClickLabel, lazyScroll
        } = this.props;
        const hourSeries = _.range(minHour, maxHour + step, step);
        return (
            <>
                <div styleName="timeline">
                    {extraContent}
                    <DailyTimelineContent rows={rows}
                                          hourSeries={hourSeries}
                                          recurrenceType={recurrenceType}
                                          onClick={onClick}
                                          itemClass={itemClass}
                                          itemProps={itemProps}
                                          longLabel={longLabel}
                                          onClickLabel={onClickLabel}
                                          isLoading={isLoading}
                                          lazyScroll={lazyScroll} />
                </div>
            </>
        );
    };

    render() {
        const {emptyMessage, rows, isLoading} = this.props;
        if (!isLoading && _.isEmpty(rows)) {
            return emptyMessage;
        }
        return this.renderTimeline();
    }
}
