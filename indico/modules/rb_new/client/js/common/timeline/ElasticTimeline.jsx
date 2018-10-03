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


/**
 * An *elastic* implementation of a Timeline, which can provide
 * an overview by day, week or month.
 */
export default class ElasticTimeline extends React.Component {
    static propTypes = {
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        datePicker: PropTypes.object.isRequired,
        isLoading: PropTypes.bool,
        itemClass: PropTypes.func,
        itemProps: PropTypes.object,
        onClickLabel: PropTypes.func,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        longLabel: PropTypes.bool,
        emptyMessage: PropTypes.node,
        lazyScroll: PropTypes.object,
        extraContent: PropTypes.node,
        showUnused: PropTypes.bool
    };

    static defaultProps = {
        emptyMessage: (
            <Message warning>
                <Translate>
                    No occurrences found
                </Translate>
            </Message>
        ),
        onClickCandidate: null,
        onClickReservation: null,
        extraContent: null,
        isLoading: false,
        itemClass: TimelineItem,
        itemProps: {},
        longLabel: false,
        onClickLabel: null,
        lazyScroll: null,
        showUnused: true
    };

    renderTimeline = () => {
        const {
            extraContent, onClickCandidate, onClickReservation, rows, isLoading, itemClass, itemProps,
            longLabel, onClickLabel, lazyScroll, datePicker: {minHour, maxHour, hourStep, mode},
            showUnused
        } = this.props;
        return (
            <>
                <div styleName="timeline">
                    {extraContent}
                    {mode === 'day' && (
                        <DailyTimelineContent rows={rows}
                                              minHour={minHour}
                                              maxHour={maxHour}
                                              hourStep={hourStep}
                                              onClickCandidate={onClickCandidate}
                                              onClickReservation={onClickReservation}
                                              itemClass={itemClass}
                                              itemProps={itemProps}
                                              longLabel={longLabel}
                                              onClickLabel={onClickLabel}
                                              isLoading={isLoading}
                                              lazyScroll={lazyScroll}
                                              showUnused={showUnused} />
                    )}
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
