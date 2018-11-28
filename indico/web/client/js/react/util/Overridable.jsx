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
import {connect} from 'react-redux';
import {withRouter} from 'react-router-dom';

/**
 * This function instantiates a React.Component with a set of additional passed props. It supports
 * `Overridable` components.
 *
 * @param {React.Component} Component - the actual component that will be parametrized
 * @param {Object|Function} extraProps - additional properties passed to the final component
 */
export function parametrize(Component, extraProps) {
    const ParametrizedComponent = ({...props}) => {
        // handle deferred prop calculation
        if (typeof extraProps === 'function') {
            extraProps = extraProps();
        }

        // Overridables will store the original component in an attribute
        if (Component.originalComponent) {
            Component = Component.originalComponent;
        }

        // extraProps override props if there is a name collision
        const {children, ...attrProps} = {...props, ...extraProps};
        return React.createElement(Component, attrProps, children);
    };
    const name = Component.displayName || Component.name;
    ParametrizedComponent.displayName = `Parametrized(${name})`;
    return ParametrizedComponent;
}

/**
 * Component that implements <Overridable />.
 */
function _OverridableComponent({id, children, overrides, ...restProps}) {
    const child = children ? React.Children.only(children) : null;
    const childProps = child ? child.props : {};
    const Override = overrides[id];

    return (Override !== undefined) ? (
        // If there's an override, we replace the component's content with
        // the override + props
        React.createElement(Override, {...childProps, ...restProps})
    ) : (
        // No override? Clone the Overridable component's original children
        child ? React.cloneElement(child, childProps) : null
    );
}

_OverridableComponent.displayName = `Overridable`;

const Overridable = connect(
    ({_overrides}) => ({
        overrides: _overrides
    })
)(_OverridableComponent);

Overridable.propTypes = {
    /** The children of the component */
    children: PropTypes.node,
    /** The id that the component will be bound to (normally component's name) */
    id: PropTypes.string
};

Overridable.defaultProps = {
    id: null,
    children: null
};

/**
 * High-order component that wraps around a normal React component and links it to
 * the central overriding mechanism.
 *
 * @param {String} id - the ID the component will be bound to (normally its name)
 * @param {React.Component} Component - the react component to be wrapped
 */
Overridable.component = (id, Component) => {
    const _Overridable = ({children, overrides, ...props}) => {
        // the logic here is simpler: the wrapped component is itself the content
        return React.createElement(overrides[id] ? overrides[id] : Component, props, children);
    };
    _Overridable.propTypes = {
        children: PropTypes.oneOfType([PropTypes.node, PropTypes.func]),
        overrides: PropTypes.object.isRequired
    };
    _Overridable.defaultProps = {
        children: null
    };
    _Overridable.displayName = `Overridable(${Component.displayName || Component.name})`;
    _Overridable.originalComponent = Component;
    return connect(
        ({_overrides}) => ({
            overrides: _overrides
        })
    )(_Overridable);
};


export default Overridable;
export const RouteAwareOverridable = withRouter(Overridable);
