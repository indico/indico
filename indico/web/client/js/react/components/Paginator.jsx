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
import IButton from "./IButton";

import './style/paginator.scss';

export default class Paginator extends React.Component {
    static propTypes = {
        currentPage: PropTypes.number.isRequired,
        pages: PropTypes.array.isRequired,
        changePage: PropTypes.func.isRequired,
    };

    render() {
        const {pages, currentPage, changePage} = this.props;

        let ellipsisKey = 0;
        function getPageKey(number) {
            return number === null ? `ellipsis-${++ellipsisKey}` : `page-${number}`;
        }

        return (
            <ul className="paginator">
                {pages.length > 1 && currentPage !== 1 && (
                    <li key="prev-page" className="page-arrow">
                        <IButton classes="icon-prev" onClick={() => changePage(currentPage - 1)} />
                    </li>
                )}
                {pages.map((number) => (
                    <li key={getPageKey(number)} className="page-number">
                        {(number === null) ? (
                            <span className="superfluous-text">…</span>
                        ) : (
                            <IButton classes={number === currentPage ? 'highlight' : ''}
                                     onClick={() => changePage(number)}>
                                {number}
                            </IButton>
                        )}
                    </li>
                ))}
                {pages.length > 1 && currentPage !== pages[pages.length - 1] && (
                    <li key="next-page" className="page-arrow">
                        <IButton classes="icon-next" onClick={() => changePage(currentPage + 1)} />
                    </li>
                )}
            </ul>
        );
    }
}
