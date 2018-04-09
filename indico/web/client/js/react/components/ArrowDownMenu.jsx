import React from 'react';
import propTypes from 'prop-types';
import {Popover, Icon} from 'antd';

import {Slot} from 'indico/react/util';

import styles from './ArrowDownMenu.module.scss';


export default function ArrowDownMenu({children}) {
    const {avatar, content} = Slot.split(children);
    const menu = content;
    return (
        <Popover content={menu} placement="bottomRight" trigger="click">
            <span styleName="container">
                {avatar}
                <Icon styleName="arrow-down-icon" type="down" size="large" />
            </span>
        </Popover>
    );
}

ArrowDownMenu.propTypes = {
    children: propTypes.node.isRequired
};

export {styles};
