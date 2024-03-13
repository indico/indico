// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment/moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
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
} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {camelizeKeys} from 'indico/utils/case';

import './NoteConflictModal.module.scss';

export function NoteConflictModal({
  currentNote,
  externalNote,
  onClose,
  setCloseAndReload,
  overwriteChanges,
}) {
  const [open, setOpen] = useState(true);

  // camelize the externalNoteSource keys
  const extNote = camelizeKeys(externalNote);

  const renderDummyNote = () => {
    return (
      <CardContent className="editor-output">
        <div styleName="blurred-note" aria-hidden>
          <h1>Dummy Notes</h1>
          <p>
            This is some dummy text that should not be seen - if you can see this text, then please,
            consider updating/and or adjust your browser settings or file a bug report.
          </p>
          <p>Lorem Ipsum</p>
          <ul>
            <li>Lorem ipsum dolor sit amet</li>
            <li>Consectetur adipiscing elit</li>
            <li>Integer molestie lorem at massa</li>
          </ul>
        </div>
      </CardContent>
    );
  };

  return (
    <Modal
      open={open}
      onClose={() => {
        setOpen(false);
        onClose();
      }}
      onOpen={() => setOpen(true)}
      size="large"
      style={{minWidth: '65vw'}}
      closeOnEscape={false}
      closeOnDimmerClick={false}
      closeIcon
    >
      <Modal.Header>
        <Translate>Conflict Detected</Translate>
      </Modal.Header>
      <Modal.Content>
        <Message warning>
          <Message.Header>
            <Translate>This note has been modified by someone else</Translate>
          </Message.Header>
          <p>
            <Translate>
              This note was last modified on{' '}
              <Param
                name="last_modified_dt"
                value={moment(extNote.createdDt).format('L LTS')}
                wrapper={<strong />}
              />{' '}
              by <Param name="note_author" value={extNote.noteAuthor} wrapper={<strong />} />
              {'. '}You can either:
            </Translate>
          </p>
          <List style={{marginTop: '0.3rem'}}>
            <List.Item>
              <List.Icon name="write" />
              <List.Content>
                <Translate>Overwrite the changes made by the other person</Translate>
              </List.Content>
            </List.Item>
            <List.Item>
              <List.Icon name="trash alternate outline" />
              <List.Content>
                <Translate>Discard your changes</Translate>
              </List.Content>
            </List.Item>
            <List.Item>
              <List.Icon name="cancel" />
              <List.Content>
                <Translate>
                  Close this message and return to the note without resolving the conflict
                </Translate>
              </List.Content>
            </List.Item>
          </List>
        </Message>

        <Grid divided="vertically" celled="internally">
          <GridRow columns={2}>
            <GridColumn>
              <Header
                as="h3"
                content={Translate.string('Your changes')}
                subheader={Translate.string('The changes you made to the note')}
              />
              <Card raised fluid>
                <CardContent>
                  <div
                    dangerouslySetInnerHTML={{__html: currentNote}}
                    className="editor-output"
                    styleName="note-content"
                  />
                </CardContent>
              </Card>
            </GridColumn>
            <GridColumn>
              <Header
                as="h3"
                content={Translate.string('Changes made by someone else')}
                subheader={Translate.string(
                  'The changes made by someone else since you started editing the note'
                )}
              />
              {!extNote.source && (
                <Message icon styleName="note-deleted-notice">
                  <Icon name="trash alternate outline" />
                  <Translate>This note revision has been deleted.</Translate>
                </Message>
              )}
              <Card raised fluid>
                {extNote.source ? (
                  <CardContent>
                    <div
                      dangerouslySetInnerHTML={{__html: extNote.source}}
                      className="editor-output"
                      styleName="note-content"
                    />
                  </CardContent>
                ) : (
                  renderDummyNote()
                )}
              </Card>
            </GridColumn>
          </GridRow>
        </Grid>
      </Modal.Content>
      <Modal.Actions>
        <Button
          content={Translate.string('Overwrite changes')}
          icon="write"
          labelPosition="left"
          negative
          onClick={async () => {
            setOpen(false);
            onClose();
            overwriteChanges();
            setCloseAndReload(true);
          }}
        />
        <Button
          content={Translate.string('Discard changes')}
          icon="trash alternate outline"
          labelPosition="right"
          onClick={() => {
            setOpen(false);
            onClose();
            setCloseAndReload(true);
          }}
        />
      </Modal.Actions>
    </Modal>
  );
}

export default NoteConflictModal;

NoteConflictModal.propTypes = {
  currentNote: PropTypes.string.isRequired,
  externalNote: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
  setCloseAndReload: PropTypes.func.isRequired,
  overwriteChanges: PropTypes.func.isRequired,
};
