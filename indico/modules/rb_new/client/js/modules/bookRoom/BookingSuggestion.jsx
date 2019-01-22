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
import {Grid, Icon, Label, Message} from 'semantic-ui-react';
import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import {Slot, IndicoPropTypes} from 'indico/react/util';

import Room from '../../components/Room';

import './BookingSuggestion.module.scss';


function SuggestionOption({onClick, overrides, icon, text}) {
    return (
        <Message styleName="suggestion-text" size="mini"
                 onClick={onClick.bind(undefined, overrides)}
                 warning compact>
            <Message.Header>
                <Icon name={icon} /> {text}
            </Message.Header>
        </Message>
    );
}

SuggestionOption.propTypes = {
    onClick: PropTypes.func.isRequired,
    overrides: PropTypes.object,
    icon: PropTypes.string.isRequired,
    text: IndicoPropTypes.i18n.isRequired
};

SuggestionOption.defaultProps = {
    overrides: null
};

/**
 * Renders a "suggested room" containing one or more alternative options
 * e.g. "10 minutes later", "Skip one day"...
 */
export default class BookingSuggestion extends React.PureComponent {
    static propTypes = {
        /** Room information */
        room: PropTypes.object.isRequired,
        /** Suggestions as {time, duration, skip} */
        suggestions: PropTypes.shape({
            time: PropTypes.number,
            duration: PropTypes.number,
            skip: PropTypes.number
        }).isRequired,
        /** Will be called when a suggestion is chosen (clicked on) */
        onClick: PropTypes.func.isRequired
    };

    renderSuggestionText(room, {time, duration, skip}) {
        const {onClick} = this.props;
        return (
            <>
                {time && (
                    <SuggestionOption onClick={onClick}
                                      overrides={{time}}
                                      icon="clock"
                                      text={(
                                          <PluralTranslate count={time}>
                                              <Singular>
                                                  One minute <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                              </Singular>
                                              <Plural>
                                                  <Param name="count" value={Math.abs(time)} /> minutes{' '}
                                                  <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                              </Plural>
                                          </PluralTranslate>
                                      )} />
                )}
                {duration && time && (
                    <div>
                        <Label color="brown" circular>{Translate.string('or')}</Label>
                    </div>
                )}
                {duration && (
                    <SuggestionOption onClick={onClick}
                                      overrides={{duration}}
                                      icon="hourglass full"
                                      text={PluralTranslate.string('One minute shorter', '{duration} minutes shorter', duration, {duration})} />
                )}
                {skip && (
                    <SuggestionOption onClick={onClick}
                                      icon="calendar times"
                                      text={PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})} />
                )}
            </>
        );
    }

    render() {
        const {room, suggestions} = this.props;
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered styleName="suggestion" columns={3}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            {this.renderSuggestionText(room, suggestions)}
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    }
}
