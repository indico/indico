// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment/moment';
import PropTypes from 'prop-types';
import React from 'react';
import {
  Card,
  CardContent,
  Header,
  Modal,
  Button,
  Message,
  Icon,
  Grid,
  GridRow,
  GridColumn,
  List,
  Segment,
  ButtonGroup,
} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {camelizeKeys} from 'indico/utils/case';

import './ConflictModal.module.scss';

export function ConflictModal({noteData, onClose}) {
  // camelize the noteData keys
  const note = camelizeKeys(noteData);

  const renderDeletedRevision = () => {
    return (
      <Segment placeholder styleName="revision-deleted">
        <Header icon>
          <Icon name="trash outline alternate" />
          <Translate>This content has been deleted.</Translate>
        </Header>
      </Segment>
    );
  };

  const renderLastModifiedDt = dt => {
    return (
      <span title={moment(dt).format('L LTS')} styleName="last-modified-text">
        {moment(dt).fromNow()}
      </span>
    );
  };

  return (
    <Modal
      open
      onClose={() => onClose(null)}
      style={{minWidth: '65vw'}}
      closeOnEscape={false}
      closeOnDimmerClick={false}
      closeIcon
    >
      <Modal.Header>
        <Translate>Conflict Detected</Translate>
      </Modal.Header>
      <Modal.Content>
        <Message warning icon>
          <Icon name="random" />
          <Message.Content>
            <Message.Header>
              <Translate>There were changes made by someone else</Translate>
            </Message.Header>
            <p>
              <Translate>
                These minutes were last modified{' '}
                <Param
                  name="last_modified_dt"
                  value={renderLastModifiedDt(note.conflict.createdDt)}
                  wrapper={<strong />}
                />{' '}
                by{' '}
                <Param name="note_author" value={note.conflict.noteAuthor} wrapper={<strong />} />
                {'. '}You can either:
              </Translate>
            </p>
            <List style={{marginTop: 0}}>
              <List.Item>
                <List.Icon name="write" />
                <List.Content>
                  <Translate>
                    Overwrite the changes made by the other person with your changes
                  </Translate>
                </List.Content>
              </List.Item>
              <List.Item>
                <List.Icon name="trash alternate outline" />
                <List.Content>
                  <Translate>
                    Discard your changes and keep the changes made by the other person
                  </Translate>
                </List.Content>
              </List.Item>
              <List.Item>
                <List.Icon name="cancel" />
                <List.Content>
                  <Translate>
                    Close this message and continue editing without resolving the conflict
                  </Translate>
                </List.Content>
              </List.Item>
            </List>
          </Message.Content>
        </Message>

        <Grid divided="vertically" celled="internally">
          <GridRow columns={2}>
            <GridColumn>
              <Header
                as="h3"
                content={Translate.string('Your changes')}
                subheader={Translate.string('The changes you are attempting to save')}
              />
              <Card raised fluid>
                <CardContent>
                  <div
                    dangerouslySetInnerHTML={{__html: note.html}}
                    className="editor-output"
                    styleName="conflict-content"
                  />
                </CardContent>
              </Card>
            </GridColumn>
            <GridColumn>
              <Header
                as="h3"
                content={Translate.string('Changes made by someone else')}
                subheader={Translate.string(
                  'The changes made by someone else since you started editing'
                )}
              />
              {note.conflict.source ? (
                <Card raised fluid>
                  <CardContent>
                    <div
                      dangerouslySetInnerHTML={{__html: note.conflict.source}}
                      className="editor-output"
                      styleName="conflict-content"
                    />
                  </CardContent>
                </Card>
              ) : (
                renderDeletedRevision()
              )}
            </GridColumn>
          </GridRow>
        </Grid>
      </Modal.Content>
      <Modal.Actions>
        <ButtonGroup styleName="action-button-icons">
          <Button icon color="red" onClick={() => onClose('overwrite')}>
            <Icon name="write" />
            <span styleName="action-button-text">
              <Translate>Overwrite their changes</Translate>
            </span>
          </Button>
          <Button icon color="orange" onClick={() => onClose('discard')}>
            <Icon name="trash alternate outline" />
            <span styleName="action-button-text">
              <Translate>Discard my changes</Translate>
            </span>
          </Button>
          <Button icon onClick={() => onClose(null)}>
            <Icon name="cancel" />
            <span styleName="action-button-text">
              <Translate>Go back to the editor</Translate>
            </span>
          </Button>
        </ButtonGroup>
      </Modal.Actions>
    </Modal>
  );
}

ConflictModal.propTypes = {
  noteData: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};
