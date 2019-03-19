/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Dropdown} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';


const isValid = value => /^\S+@\S+\.\S+$/.test(value);


/**
 * A field that lets the user enter email addresses
 */
const EmailListField = (props) => {
    const {value, disabled, onChange, onFocus, onBlur} = props;
    const [options, setOptions] = useState(value.filter(isValid).map(x => ({text: x, value: x})));

    const handleChange = (e, {value: newValue}) => {
        newValue = _.uniq(newValue.filter(isValid));
        setOptions(newValue.map(x => ({text: x, value: x})));
        onChange(newValue);
        onFocus();
        onBlur();
    };

    return (
        <Dropdown options={options}
                  value={value}
                  disabled={disabled}
                  searchInput={{onFocus, onBlur, type: 'email'}}
                  search selection multiple allowAdditions fluid closeOnChange
                  noResultsMessage={Translate.string('Please enter an email address')}
                  placeholder={Translate.string('Please enter an email address')}
                  additionLabel={Translate.string('Add email') + ' '} // eslint-disable-line prefer-template
                  onChange={handleChange} />
    );
};

EmailListField.propTypes = {
    value: PropTypes.arrayOf(PropTypes.string).isRequired,
    disabled: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
};


export default React.memo(EmailListField);
