// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import speakerLinkURL from 'indico-url:persons.api_speaker_link';
import speakerLinksURL from 'indico-url:persons.api_speaker_links';

import {AxiosError} from 'axios';
import React, {useCallback, useEffect, useRef, useState} from 'react';
import ReactDOM from 'react-dom';
import {
  Modal,
  Button,
  Icon,
  SemanticICONS,
  Table,
  Popup,
  Loader,
  Dropdown,
} from 'semantic-ui-react';
import * as SUI from 'semantic-ui-react/dist/es/lib/SUI';

import {FinalDropdown, FinalInput} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxiosWithMutation} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import {SpeakerLink} from './types';

import './SpeakerLinks.module.scss';

function makeTitle(s: string) {
  return s
    .split(' ')
    .map(word =>
      word.length === 0 ? word : word.charAt(0).toLocaleUpperCase() + word.substring(1)
    )
    .join(' ');
}

const ICON_OPTIONS = SUI.ICONS_AND_ALIASES.map((iconName: string) => ({
  key: iconName,
  value: iconName,
  icon: iconName,
  text: makeTitle(iconName),
}));

export const DEFAULT_SOCIAL_ICONS: Record<string, SemanticICONS> = {
  Facebook: 'facebook',
  LinkedIn: 'linkedin',
  GitHub: 'github',
  Webpage: 'world',
};

type NewSpeakerLink = Omit<SpeakerLink, 'id'>;

type ModalType = 'MANAGE_LINKS' | 'EDIT_LINK' | 'CREATE_LINK';

export function SpeakerLinks({eventId}: {eventId: number}) {
  const manageSpeakerLinksRef = useRef<HTMLAnchorElement>(null);
  const [openModal, setOpenModal] = useState<ModalType | null>(null);
  const [initialCreateOrEditLinkFormValues, setInitialCreateOrEditLinkFormValues] =
    useState<SpeakerLink>();
  const {
    data: speakerLinks,
    loading,
    mutate,
    mutationError,
  } = useIndicoAxiosWithMutation<SpeakerLink[]>({
    url: speakerLinksURL({event_id: eventId}),
  });

  const manageSpeakerLinks = useCallback((event: React.MouseEvent<HTMLAnchorElement>) => {
    event.stopPropagation();
    setOpenModal('MANAGE_LINKS');
  }, []);

  const openCreateSpeakerLinkModal = useCallback(() => {
    setInitialCreateOrEditLinkFormValues(undefined);
    setOpenModal('CREATE_LINK');
  }, []);

  const openEditSpeakerLinkModal = useCallback((link: SpeakerLink) => {
    setInitialCreateOrEditLinkFormValues(link);
    setOpenModal('EDIT_LINK');
  }, []);

  const addSpeakerLink = useCallback(
    (link: NewSpeakerLink) => {
      mutate(indicoAxios.put(speakerLinksURL({event_id: eventId}), link), data => [
        ...data,
        {...link, id: -1},
      ]);
    },
    [mutate, eventId]
  );

  const editSpeakerLink = useCallback(
    (link: SpeakerLink) => {
      mutate(
        indicoAxios.patch(speakerLinkURL({event_id: eventId, speaker_link_id: link.id}), link),
        data => [...data.filter(l => l.id !== link.id), {...link}]
      );
    },
    [mutate, eventId]
  );

  const removeSpeakerLink = useCallback(
    (link: SpeakerLink) => {
      mutate(
        indicoAxios.delete(speakerLinkURL({event_id: eventId, speaker_link_id: link.id})),
        data => data.filter(l => l.id !== link.id)
      );
    },
    [mutate, eventId]
  );

  const handleCreateSpeakerLink = useCallback(
    (formData: NewSpeakerLink) => {
      addSpeakerLink(formData);
      setOpenModal('MANAGE_LINKS');
    },
    [addSpeakerLink]
  );

  const handleEditSpeakerLink = useCallback(
    (formData: SpeakerLink) => {
      editSpeakerLink(formData);
      setOpenModal('MANAGE_LINKS');
    },
    [editSpeakerLink]
  );

  useEffect(() => {
    const triggerElement = manageSpeakerLinksRef.current;
    if (triggerElement === null || speakerLinks === null) {
      return;
    }
    triggerElement.dispatchEvent(
      new CustomEvent('indico:speakerLinksUpdate', {
        detail: speakerLinks,
        bubbles: true,
      })
    );
  }, [speakerLinks]);

  useEffect(() => {
    if (!mutationError || !(mutationError as AxiosError).isAxiosError) {
      return;
    }
    handleAxiosError(mutationError);
  }, [mutationError]);

  return (
    <>
      <a
        onClick={manageSpeakerLinks}
        className="i-button borderless icon-settings js-button"
        ref={manageSpeakerLinksRef}
      >
        {Translate.string('Settings')}
      </a>
      {loading || speakerLinks === null ? (
        <Loader />
      ) : (
        <>
          <Modal
            open={openModal !== null}
            onClose={() => setOpenModal(null)}
            onSubmit={undefined}
            closeIcon
          >
            <Translate as={Modal.Header}>Manage Speaker Links</Translate>
            <Modal.Content>
              <div>
                <Table>
                  <Table.Header>
                    <Table.Row>
                      {speakerLinks?.length === 0 ? (
                        <Table.HeaderCell colSpan={2}>
                          <Translate>There are no link types associated with this event.</Translate>
                        </Table.HeaderCell>
                      ) : (
                        <>
                          <Translate as={Table.HeaderCell}>Name</Translate>
                          <Table.HeaderCell width={1} />
                        </>
                      )}
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {speakerLinks.map(link => (
                      <Table.Row key={link.id}>
                        <Table.Cell>
                          <Icon name={link.icon as SemanticICONS} />
                          {link.name}
                        </Table.Cell>
                        <Table.Cell>
                          <div className="row">
                            <Popup
                              content={Translate.string('Edit speaker link')}
                              position="top center"
                              trigger={
                                <Icon
                                  name="edit"
                                  link
                                  onClick={() => openEditSpeakerLinkModal(link)}
                                />
                              }
                            />
                            <Popup
                              content={Translate.string('Delete speaker link')}
                              position="top center"
                              trigger={
                                <Icon
                                  name="trash"
                                  link
                                  color="red"
                                  onClick={() => removeSpeakerLink(link)}
                                />
                              }
                            />
                          </div>
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                  <Table.Footer>
                    <Table.Row>
                      <Table.HeaderCell colSpan="2">
                        <Dropdown
                          text={Translate.string('Add new link type')}
                          icon="add"
                          labeled
                          button
                          className="icon"
                        >
                          <Dropdown.Menu>
                            {Object.keys(DEFAULT_SOCIAL_ICONS).map(name => (
                              <Dropdown.Item
                                key={name}
                                icon={DEFAULT_SOCIAL_ICONS[name]}
                                text={name}
                                disabled={
                                  speakerLinks.find(link => link.name === name) !== undefined
                                }
                                onClick={() =>
                                  addSpeakerLink({name, icon: DEFAULT_SOCIAL_ICONS[name]})
                                }
                              />
                            ))}
                            <Dropdown.Item
                              text={Translate.string('Create custom...')}
                              onClick={openCreateSpeakerLinkModal}
                            />
                          </Dropdown.Menu>
                        </Dropdown>
                      </Table.HeaderCell>
                    </Table.Row>
                  </Table.Footer>
                </Table>
              </div>
            </Modal.Content>
            <Modal.Actions>
              <Button onClick={() => setOpenModal(null)} content={Translate.string('Close')} />
            </Modal.Actions>
          </Modal>
          {(openModal === 'CREATE_LINK' || openModal === 'EDIT_LINK') && (
            <FinalModalForm
              id="edit-or-create-link-form"
              onClose={() => setOpenModal('MANAGE_LINKS')}
              onSubmit={
                openModal === 'CREATE_LINK' ? handleCreateSpeakerLink : handleEditSpeakerLink
              }
              size="small"
              initialValues={initialCreateOrEditLinkFormValues}
              header={
                openModal === 'CREATE_LINK'
                  ? Translate.string('Create Speaker Link')
                  : Translate.string('Edit Speaker Link')
              }
            >
              <FinalInput name="name" required fluid label={Translate.string('Name')} />
              <FinalDropdown
                name="icon"
                required
                label={Translate.string('Icon')}
                placeholder={Translate.string('Select Icon')}
                labeled
                fluid
                search
                selection
                options={ICON_OPTIONS}
              />
            </FinalModalForm>
          )}
        </>
      )}
    </>
  );
}

customElements.define(
  'ind-manage-speaker-links',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <SpeakerLinks eventId={JSON.parse(this.getAttribute('event-id') ?? '')} />,
        this
      );
    }
  }
);
