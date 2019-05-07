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
import {Item, Placeholder} from 'semantic-ui-react';


export default function ItemPlaceholder() {
    return (
        <Item>
            <Item.Image>
                <Placeholder>
                    <Placeholder.Image />
                </Placeholder>
            </Item.Image>
            <Item.Content>
                <Placeholder>
                    <Placeholder.Line length="very short" />
                </Placeholder>
                <Item.Meta>
                    <Placeholder>
                        <Placeholder.Line length="short" />
                    </Placeholder>
                </Item.Meta>
                <Item.Description>
                    <Placeholder>
                        <Placeholder.Line length="full" />
                        <Placeholder.Line length="full" />
                    </Placeholder>
                </Item.Description>
            </Item.Content>
        </Item>
    );
}

function ItemPlaceholderGroup({count}) {
    return (
        <Item.Group>
            {_.range(0, count).map((i) => (
                <ItemPlaceholder key={i} />
            ))}
        </Item.Group>
    );
}

ItemPlaceholderGroup.propTypes = {
    count: PropTypes.number.isRequired,
};

ItemPlaceholder.Group = ItemPlaceholderGroup;
