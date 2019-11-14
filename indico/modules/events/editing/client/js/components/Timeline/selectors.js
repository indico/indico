// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';

export function processDetails(details) {
  const {revisions} = details;
  const newRevisions = [];
  const revisionsIterator = revisions[Symbol.iterator]();

  for (const revision of revisionsIterator) {
    if (revision.finalState.name === 'replaced') {
      const nextRevision = revisionsIterator.next().value;
      const customItem = {
        createdDt: nextRevision.createdDt,
        id: `revision-${nextRevision.id}`,
        system: false,
        text: nextRevision.comment,
        html: nextRevision.commentHtml,
        user: nextRevision.submitter,
        custom: true,
        header: Translate.string('Revision has been replaced'),
        state: 'replaced',
      };

      newRevisions.push({
        ...revision,
        items: [...revision.comments, customItem, ...nextRevision.comments],
      });
    } else {
      newRevisions.push({...revision, items: revision.comments});
    }
  }

  return {...details, revisions: newRevisions};
}
