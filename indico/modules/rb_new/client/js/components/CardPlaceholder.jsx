import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Card, Placeholder} from 'semantic-ui-react';


export default function CardPlaceholder() {
    return (
        <Card>
            <Placeholder>
                <Placeholder.Image />
            </Placeholder>
            <Card.Content>
                <Placeholder>
                    <Placeholder.Header>
                        <Placeholder.Line length="very short" />
                        <Placeholder.Line length="medium" />
                    </Placeholder.Header>
                    <Placeholder.Paragraph>
                        <Placeholder.Line length="short" />
                    </Placeholder.Paragraph>
                </Placeholder>
            </Card.Content>
            <Card.Content extra>
                <Placeholder>
                    <Placeholder.Line length="short" />
                </Placeholder>
            </Card.Content>
        </Card>
    );
}

function CardPlaceholderGroup({count, className}) {
    const props = className ? {className} : {};
    return (
        <Card.Group {...props} stackable>
            {_.range(0, count).map((i) => (
                <CardPlaceholder key={i} />
            ))}
        </Card.Group>
    );
}

CardPlaceholderGroup.propTypes = {
    count: PropTypes.number.isRequired,
    className: PropTypes.string
};

CardPlaceholderGroup.defaultProps = {
    className: null
};

CardPlaceholder.Group = CardPlaceholderGroup;
