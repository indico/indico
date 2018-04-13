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
import {Input, Select} from 'antd';
import propTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

import './TextSearch.module.scss';


export default function TextSearch({setTextFilter}) {
    const selectBefore = (
        <Select defaultValue="Filters" styleName="filters-select">
            <Select.Option value="name">
                <Translate>Name</Translate>
            </Select.Option>
            <Select.Option value="building">
                <Translate>Building</Translate>
            </Select.Option>
        </Select>
    );

    return (
        <div styleName="text-filter">
            <Input addonBefore={selectBefore} onChange={(e) => setTextFilter(e.target.value)} />
        </div>
    );
}

TextSearch.propTypes = {
    setTextFilter: propTypes.func.isRequired
};
