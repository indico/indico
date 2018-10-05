import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {withRouter} from 'react-router-dom';


function Overridable({children, overrides, id, ...restProps}) {
    const child = children ? React.Children.only(children) : null;
    const childProps = child ? child.props : {};
    const Override = overrides[id];

    return (Override !== undefined) ? (
        <Override {...childProps} {...restProps} />
    ) : (
        child ? React.cloneElement(child, childProps) : null
    );
}

Overridable.propTypes = {
    children: PropTypes.node,
    overrides: PropTypes.object.isRequired,
    id: PropTypes.string
};

Overridable.defaultProps = {
    id: null,
    children: null
};

const ConnectedOverriable = connect(({_overrides}) => ({
    overrides: _overrides
}))(Overridable);


export default ConnectedOverriable;
export const RouteAwareOverridable = withRouter(ConnectedOverriable);
