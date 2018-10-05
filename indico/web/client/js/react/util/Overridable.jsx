import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {withRouter} from 'react-router-dom';


function Overridable({children, overrides, id, ...restProps}) {
    const childProps = children ? children.props : {};
    const Override = overrides[id];
    const newProps = {...restProps, ...childProps};

    return (Override !== undefined) ? (
        <Override {...newProps} />
    ) : (
        !!children && React.cloneElement(children, {...newProps})
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
