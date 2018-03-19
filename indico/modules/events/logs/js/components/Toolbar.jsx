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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';

import Filter from '../containers/Filter';
import SearchBox from '../containers/SearchBox';


class Toolbar extends React.Component {
    static propTypes = {
        realms: PropTypes.object.isRequired,
    };

    render() {
        const {realms} = this.props;
        return (
            <div className="follow-scroll toolbars">
                <Filter realms={realms} />
                <SearchBox />
            </div>
        );
    }
}

const mapStateToProps = ({staticData}) => ({
    realms: staticData.realms,
});

export default connect(mapStateToProps)(Toolbar);
