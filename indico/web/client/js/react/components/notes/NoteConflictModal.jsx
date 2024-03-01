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
  Grid,
  GridRow,
  GridColumn,
  List,
} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';

export function NoteConflictModal({currentNoteSource, externalNoteSource}) {
  const [open, setOpen] = useState(true);
  console.log('externalNoteSource', externalNoteSource);

  /* const handleClose = () => {
    setOpen(false);
  };

  const handleOpen = () => {
    setOpen(true);
  }; */

  /*
   * TODO:
   *  - Add another button to cancel the dialog (close and return back without doing anything?) (need to fix this!)
   *  - Fix saving!!!
   *  - Actions for the buttons
   */
  return (
    <Modal
      open={open}
      onClose={() => setOpen(false)}
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
            <Translate>This note has been edited by someone else</Translate>
          </Message.Header>
          <p>
            <Translate>
              This note was last edited on{' '}
              <Param
                name="last_edited_dt"
                value={moment(externalNoteSource.createdDt).format('L LTS')}
                wrapper={<strong />}
              />{' '}
              by{' '}
              <Param
                name="note_author"
                value={externalNoteSource.noteAuthor}
                wrapper={<strong />}
              />
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
                    dangerouslySetInnerHTML={{__html: currentNoteSource}}
                    className="editor-output"
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
              <Card raised fluid>
                <CardContent>
                  <div
                    dangerouslySetInnerHTML={{__html: externalNoteSource.source}}
                    className="editor-output"
                  />
                </CardContent>
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
        />
        <Button
          content={Translate.string('Discard changes')}
          icon="trash alternate outline"
          labelPosition="right"
        />
      </Modal.Actions>
    </Modal>
  );
}

export default NoteConflictModal;

NoteConflictModal.propTypes = {
  currentNoteSource: PropTypes.string.isRequired,
  externalNoteSource: PropTypes.object.isRequired,
};
