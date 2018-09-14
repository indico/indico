import React from 'react';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';


function Overridable({children, overrides, id, ...restProps}) {
    const childProps = children.props;
    const Override = overrides[id];
    const newProps = {...restProps, ...childProps};

    return (Override !== undefined) ? (
        <Override {...newProps} />
    ) : (
        React.cloneElement(children, {...newProps})
    );
}

Overridable.propTypes = {
    children: PropTypes.node.isRequired,
    overrides: PropTypes.object.isRequired,
    id: PropTypes.string
};

Overridable.defaultProps = {
    id: null
};

export default connect(({_overrides}) => ({
    overrides: _overrides
}))(Overridable);
