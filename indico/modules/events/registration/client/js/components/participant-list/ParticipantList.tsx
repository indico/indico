// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import participantListPreviewURL from 'indico-url:event_registration.manage_participant_list_preview';

import React from 'react';
import {Button, Divider, Header, HeaderContent} from 'semantic-ui-react';
import HeaderSubHeader from 'semantic-ui-react/dist/commonjs/elements/Header/HeaderSubheader';

import {PluralTranslate, Translate, Plural, Singular, Param} from 'indico/react/i18n';

import ParticipantAccordion from './ParticipantAccordion';
import {ParticipantListProps} from './types';

import './ParticipantList.module.scss';

// TODO: Implement this Jinja logic here
// {% block title %} 💚
//     {%- if not preview -%}
//         {{- page_title -}}
//     {%- else -%}
//         {% trans %}Participant List Preview{% endtrans %}
//     {%- endif -%}
// {% endblock %}

// {% block subtitle %} 💚
//     {% if num_participants %}
//         {%- trans num=num_participants %}1 participant{% pluralize %}{{ num }} participants{% endtrans -%}
//     {% endif %}
// {% endblock %} #}

// {# {% block description %}
//     {%- if preview == 'guest' -%}
//         {% trans -%}
//             This preview shows the participant list like an unregistered guest would see it.
//         {%- endtrans %}
//         <br>
//         <a href="{{ url_for('.manage_participant_list_preview', event) }}">
//             {%- trans %}Show registered participant view instead.{% endtrans -%}
//         </a>
//     {% elif preview %}
//         {% trans -%}
//             This preview shows the participant list like a registered participant would see it.
//         {%- endtrans %}
//         <br>
//         <a href="{{ url_for('.manage_participant_list_preview', event, guest=1) }}">
//             {%- trans %}Show unregistered guest view instead.{% endtrans -%}
//         </a>
//     {%- elif tables|length > 1 -%}
//         {% trans -%}
//             The lists of participants grouped by the registration form they used to register for the event.
//         {%- endtrans %}
//     {%- endif -%}
// {% endblock %}

export default function ParticipantList({
  published,
  totalParticipantCount,
  tables,
  preview,
  title,
  eventId,
}: ParticipantListProps) {
  let description, viewToggle;

  if (preview === 'guest') {
    description = (
      <Translate>
        This preview shows the participant list like an unregistered guest would see it.
      </Translate>
    );
    viewToggle = (
      <Button
        basic
        color="blue"
        icon="user"
        href={participantListPreviewURL({event_id: eventId})}
        className="view-toggle"
        content={<Translate>Show registered guest view instead.</Translate>}
      />
    );
  } else if (preview) {
    description = (
      <Translate>
        This preview shows the participant list like a registered participant would see it.
      </Translate>
    );
    viewToggle = (
      <Button
        basic
        color="blue"
        icon="user secret"
        href={participantListPreviewURL({event_id: eventId, guest: 1})}
        className="view-toggle"
        content={<Translate>Show unregistered guest view instead.</Translate>}
      />
    );
  } else if (tables.length > 1) {
    description = (
      <Translate>
        The lists of participants grouped by the registration form they used to register for the
        event.
      </Translate>
    );
  }

  return (
    <section>
      <Header as="h2" color="blue">
        <HeaderContent>
          {preview ? title : <Translate>Participant List Preview</Translate>}
        </HeaderContent>
        <HeaderSubHeader>
          <PluralTranslate count={totalParticipantCount}>
            <Singular>
              <Param name="count" value={totalParticipantCount} /> participant
            </Singular>
            <Plural>
              <Param name="count" value={totalParticipantCount} /> participants
            </Plural>
          </PluralTranslate>
        </HeaderSubHeader>
        <Divider />
        {description && <HeaderSubHeader content={description} />}
      </Header>
      {viewToggle}
      <ParticipantAccordion
        published={published}
        totalParticipantCount={totalParticipantCount}
        tables={tables}
      />
    </section>
  );
}
