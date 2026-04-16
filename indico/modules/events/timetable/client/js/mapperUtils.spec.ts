// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';

import {mapDataToEntry, mapDataToSession, mapEntryToData, mapSessionToData} from './mapperUtils';
import {BlockEntry, BreakEntry, ContribEntry, EntryType, PersonLink, Session} from './types';

const dataLocationData = {
  address: 'Avenue du Jura',
  inheriting: true,
  room_id: 1,
  room_name: 'cool room',
  venue_id: 5,
  venue_name: 'hello',
};

const entryLocationData = {
  address: 'Avenue du Jura',
  inheriting: true,
  roomId: 1,
  roomName: 'cool room',
  venueId: 5,
  venueName: 'hello',
};

const dataPersonLink = {
  address: '',
  affiliation: '',
  affiliation_id: null,
  avatar_url: '/user/1/picture-default/xxx',
  display_order: 0,
  email: 'john.doe@cern.ch',
  first_name: 'John',
  last_name: 'Doe',
  name: 'John Doe',
  person_id: 1,
  phone: '+3131313131',
  title: null,
  user_id: 1,
  user_identifier: 'User:1:xxx',
};

const entryPersonLink: PersonLink = {
  address: '',
  affiliation: '',
  affiliationId: null,
  avatarURL: '/user/1/picture-default/xxx',
  displayOrder: 0,
  email: 'john.doe@cern.ch',
  firstName: 'John',
  lastName: 'Doe',
  name: 'John Doe',
  personId: 1,
  phone: '+3131313131',
  title: null,
  userId: 1,
  userIdentifier: 'User:1:xxx',
};

describe('mapperUtils', () => {
  describe('mapDataToEntry', () => {
    it('should map Contribution fields correctly', () => {
      const data = {
        id: 101,
        type: EntryType.Contribution,
        title: 'Contribution Title',
        description: 'Contribution Desc',
        board_number: 'C1',
        person_links: [dataPersonLink],
        location_data: dataLocationData,
        keywords: ['physics'],
        session_id: 5,
        duration: 120,
        start_dt: '2024-01-01T09:00:00Z',
      };

      const entry = mapDataToEntry(data) as ContribEntry;

      expect(entry.id).toBe('c101');
      expect(entry.objId).toBe(101);
      expect(entry.type).toBe(EntryType.Contribution);
      expect(entry.title).toBe('Contribution Title');
      expect(entry.description).toBe('Contribution Desc');
      expect(entry.boardNumber).toBe('C1');
      expect(entry.personLinks).toEqual([entryPersonLink]);
      expect(entry.locationData).toEqual(entryLocationData);
      expect(entry.keywords).toEqual(['physics']);
      expect(entry.sessionId).toBe(5);
      expect(entry.duration).toBe(2);
      expect(moment.isMoment(entry.startDt)).toBe(true);
    });

    it('should map Session Block fields correctly', () => {
      const data = {
        id: 202,
        type: EntryType.SessionBlock,
        title: 'Session Block Title',
        description: 'Session Block Desc',
        session_id: 7,
        location_data: dataLocationData,
        duration: 120,
        start_dt: '2024-01-02T10:00:00Z',
      };

      const entry = mapDataToEntry(data) as BlockEntry;

      expect(entry.id).toBe('s202');
      expect(entry.objId).toBe(202);
      expect(entry.type).toBe(EntryType.SessionBlock);
      expect(entry.title).toBe('Session Block Title');
      expect(entry.description).toBe('Session Block Desc');
      expect(entry.sessionId).toBe(7);
      expect(entry.locationData).toEqual(entryLocationData);
      expect(entry.duration).toBe(2);
      expect(moment.isMoment(entry.startDt)).toBe(true);
    });

    it('should map Break fields correctly', () => {
      const data = {
        id: 303,
        type: EntryType.Break,
        title: 'Break Title',
        description: 'Break Desc',
        duration: 30,
        start_dt: '2024-01-03T11:00:00Z',
        location_data: dataLocationData,
        colors: {background: '#eeeeee', text: '#ffffff'},
      };

      const entry = mapDataToEntry(data);

      expect(entry.id).toBe('b303');
      expect(entry.objId).toBe(303);
      expect(entry.type).toBe(EntryType.Break);
      expect(entry.title).toBe('Break Title');
      expect(entry.description).toBe('Break Desc');
      expect(entry.duration).toBe(0.5);
      expect(moment.isMoment(entry.startDt)).toBe(true);
      expect(entry.locationData).toEqual(entryLocationData);
      expect(entry.colors).toEqual({backgroundColor: '#eeeeee', color: '#ffffff'});
    });
  });

  describe('mapEntryToData', () => {
    it('should map Contribution entry to API data', () => {
      const entry: ContribEntry = {
        id: 'c101',
        objId: 101,
        type: EntryType.Contribution,
        title: 'Contribution Title',
        description: 'Contribution Desc',
        boardNumber: 'C1',
        personLinks: [entryPersonLink],
        locationData: entryLocationData,
        keywords: ['physics'],
        colors: {backgroundColor: '#ffffff', color: '#303030'},
        sessionId: 5,
        duration: 1.5,
        startDt: moment('2024-01-01T09:00:00Z'),
        y: 0,
        column: 0,
        maxColumn: 0,
      };
      const data = mapEntryToData(entry);

      expect(data.id).toBe(101);
      expect(data.type).toBe(EntryType.Contribution);
      expect(data.title).toBe('Contribution Title');
      expect(data.description).toBe('Contribution Desc');
      expect(data.board_number).toBe('C1');
      expect(data.person_links).toEqual([dataPersonLink]);
      expect(data.location_data).toEqual(dataLocationData);
      expect(data.keywords).toEqual(['physics']);
      expect(data.colors).toEqual({background: '#ffffff', text: '#303030'});
      expect(data.session_id).toBe(5);
      expect(data.duration).toBe(90);
      expect(data.start_dt).toBe('2024-01-01T09:00:00.000Z');
    });

    it('should map Session Block entry to API data', () => {
      const entry: BlockEntry = {
        id: 's202',
        objId: 202,
        children: [],
        personLinks: [entryPersonLink],
        type: EntryType.SessionBlock,
        title: 'Session Block Title',
        description: 'Session Block Desc',
        sessionId: 7,
        locationData: entryLocationData,
        duration: 2,
        startDt: moment('2024-01-02T10:00:00Z'),
        colors: {backgroundColor: '#000000', color: '#ddd000'},
        childLocationParent: null,
        y: 0,
        column: 0,
        maxColumn: 0,
      };
      const data = mapEntryToData(entry);

      expect(data.id).toBe(202);
      expect(data.type).toBe(EntryType.SessionBlock);
      expect(data.title).toBe('Session Block Title');
      expect(data.description).toBe('Session Block Desc');
      expect(data.session_id).toBe(7);
      expect(data.location_data).toEqual(dataLocationData);
      expect(data.duration).toBe(120);
      expect(data.start_dt).toBe('2024-01-02T10:00:00.000Z');
      expect(data.conveners).toEqual([dataPersonLink]);
      expect(data.colors).toEqual({background: '#000000', text: '#ddd000'});
    });

    it('should map Break entry to API data', () => {
      const entry: BreakEntry = {
        id: 'b303',
        objId: 303,
        type: EntryType.Break,
        title: 'Break Title',
        description: 'Break Desc',
        duration: 0.5,
        startDt: moment('2024-01-03T11:00:00Z'),
        locationData: entryLocationData,
        colors: {backgroundColor: '#efefef', color: '#fefefe'},
        personLinks: [],
        y: 0,
        column: 0,
        maxColumn: 0,
      };
      const data = mapEntryToData(entry);

      expect(data.id).toBe(303);
      expect(data.type).toBe(EntryType.Break);
      expect(data.title).toBe('Break Title');
      expect(data.description).toBe('Break Desc');
      expect(data.duration).toBe(30);
      expect(data.start_dt).toBe('2024-01-03T11:00:00.000Z');
      expect(data.location_data).toEqual(dataLocationData);
      expect(data.colors).toEqual({background: '#efefef', text: '#fefefe'});
    });
  });

  describe('mapDataToSession', () => {
    it('should map API session data to Session object', () => {
      const data = {
        id: 11,
        title: 'Session Title',
        is_poster: true,
        colors: {background: '#112233', text: '#445566'},
        default_contribution_duration: 1500,
      };

      const session = mapDataToSession(data) as Session;

      expect(session.id).toBe(11);
      expect(session.title).toBe('Session Title');
      expect(session.isPoster).toBe(true);
      expect(session.colors).toEqual({backgroundColor: '#112233', color: '#445566'});
      expect(session.defaultContribDurationMinutes).toBe(25);
    });
  });

  describe('mapSessionToData', () => {
    it('should map Session object to API session data', () => {
      const session: Session = {
        id: 22,
        title: 'Another Session',
        isPoster: false,
        colors: {backgroundColor: '#aabbcc', color: '#ddeeff'},
        defaultContribDurationMinutes: 10,
      };

      const data = mapSessionToData(session);

      expect(data.id).toBe(22);
      expect(data.title).toBe('Another Session');
      expect(data.is_poster).toBe(false);
      expect(data.colors).toEqual({background: '#aabbcc', text: '#ddeeff'});
      expect(data.default_contribution_duration).toBe(600);
    });
  });
});
