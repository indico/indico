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
import {Button, Popconfirm, Tooltip} from 'antd';

import {Translate} from 'indico/react/i18n';

import './FilterOptions.module.scss';


export default class FilterOptions extends Popconfirm {
    renderPopup() {
        const {prefixCls, title, cancelText, okText, okType} = this.props;
        return (
            <div styleName="filter-options">
                <div className={`${prefixCls}-inner-content`}>
                    <div className={`${prefixCls}-message`}>
                        <div className={`${prefixCls}-message-title`}>{title}</div>
                    </div>
                    <div className={`${prefixCls}-buttons`}>
                        <Button onClick={this.onCancel} size="small">
                            {cancelText || <Translate>Cancel</Translate>}
                        </Button>
                        <Button onClick={this.onConfirm} type={okType} size="small">
                            {okText || <Translate>OK</Translate>}
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    render() {
        const {prefixCls, placement, ...restProps} = this.props;
        const overlay = this.renderPopup();
        return (
            <Tooltip {...restProps}
                     arrowPointAtCenter
                     prefixCls={prefixCls}
                     placement={placement}
                     onVisibleChange={this.onVisibleChange}
                     visible={this.state.visible}
                     overlay={overlay}
                     ref={this.saveTooltip} />
        );
    }
}
