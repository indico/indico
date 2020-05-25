// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {combineReducers} from 'redux';

import {camelizeKeys} from 'indico/utils/case';
import {requestReducer} from 'indico/utils/redux';
import * as actions from './actions';
import * as globalActions from '../../actions';
import {roomSearchReducerFactory} from '../../common/roomSearch/reducers';
import {initialDatePickerState} from '../../common/timeline/reducers';

export const initialTimelineState = {
  availability: [],
  isVisible: false,
  /** Rooms currently visible */
  roomIds: [],
  /** Here, parameters are saved for future requests (other rooms) */
  params: null,
};

const datePickerReducer = (state = initialDatePickerState, action) => {
  switch (action.type) {
    case actions.SET_TIMELINE_MODE:
      return {
        ...state,
        mode: action.mode,
      };
    case actions.SET_TIMELINE_DATE:
      return {
        ...state,
        selectedDate: action.date,
      };
    case actions.INIT_TIMELINE:
      return {
        ...state,
        dateRange: [],
        selectedDate: action.params.dates.startDate,
      };
    case actions.TIMELINE_RECEIVED:
      return {
        ...state,
        dateRange: action.data.date_range,
      };
    default:
      return state;
  }
};

const timelineReducer = combineReducers({
  request: requestReducer(
    actions.GET_TIMELINE_REQUEST,
    actions.GET_TIMELINE_SUCCESS,
    actions.GET_TIMELINE_ERROR
  ),
  datePicker: datePickerReducer,
  data: (state = initialTimelineState, action) => {
    switch (action.type) {
      case actions.TOGGLE_TIMELINE_VIEW:
        return {...state, isVisible: action.visible};
      case globalActions.RESET_PAGE_STATE:
        return action.namespace === 'bookRoom' ? {...state, isVisible: false} : state;
      case actions.INIT_TIMELINE:
        return {
          ...state,
          availability: [],
          params: action.params,
          roomIds: action.roomIds,
        };
      case actions.ADD_TIMELINE_ROOMS:
        return {
          ...state,
          roomIds: state.roomIds.concat(action.roomIds),
        };
      case actions.TIMELINE_RECEIVED:
        return {
          ...state,
          availability: state.availability.concat(camelizeKeys(action.data.availability)),
        };
      case actions.CREATE_BOOKING_SUCCESS: {
        const {
          data: {
            room_id: roomId,
            booking: {is_accepted: isAccepted},
          },
        } = action;
        const {roomIds, availability} = state;
        if (!isAccepted) {
          const newAvailability = availability.map(([id, roomAvailability]) => {
            if (id === roomId) {
              return [id, {...roomAvailability, preConflicts: roomAvailability.candidates}];
            }
            return [id, roomAvailability];
          });
          return {
            ...state,
            availability: newAvailability,
          };
        }
        return {
          ...state,
          roomIds: roomIds.filter(id => id !== roomId),
          availability: availability.filter(([id]) => id !== roomId),
        };
      }
      default:
        return state;
    }
  },
});

const unavailableDatePickerReducer = (state = initialDatePickerState, action) => {
  switch (action.type) {
    case actions.SET_UNAVAILABLE_NAV_MODE:
      return {
        ...state,
        mode: action.mode,
      };
    case actions.SET_UNAVAILABLE_NAV_DATE:
      return {
        ...state,
        selectedDate: action.date,
      };
    case actions.INIT_UNAVAILABLE_TIMELINE:
      return {
        ...state,
        selectedDate: action.selectedDate,
        mode: action.mode,
      };
    case actions.UNAVAILABLE_TIMELINE_RECEIVED:
      return {
        ...state,
        dateRange: action.data.date_range,
      };
    default:
      return state;
  }
};

const unavailableReducer = combineReducers({
  request: requestReducer(
    actions.GET_UNAVAILABLE_TIMELINE_REQUEST,
    actions.GET_UNAVAILABLE_TIMELINE_SUCCESS,
    actions.GET_UNAVAILABLE_TIMELINE_ERROR
  ),
  datePicker: unavailableDatePickerReducer,
  data: (state = [], action) => {
    switch (action.type) {
      case actions.GET_UNAVAILABLE_TIMELINE_REQUEST:
        return [];
      case actions.UNAVAILABLE_TIMELINE_RECEIVED:
        return camelizeKeys(action.data.availability);
      default:
        return state;
    }
  },
});

const suggestionsReducer = combineReducers({
  request: requestReducer(
    actions.FETCH_SUGGESTIONS_REQUEST,
    actions.FETCH_SUGGESTIONS_SUCCESS,
    actions.FETCH_SUGGESTIONS_ERROR
  ),
  data: (state = [], action) => {
    switch (action.type) {
      case actions.RESET_SUGGESTIONS:
        return [];
      case actions.SUGGESTIONS_RECEIVED:
        return action.data;
      default:
        return state;
    }
  },
});

const bookingFormReducer = combineReducers({
  requests: combineReducers({
    booking: requestReducer(
      actions.CREATE_BOOKING_REQUEST,
      actions.CREATE_BOOKING_SUCCESS,
      actions.CREATE_BOOKING_FAILED
    ),
    timeline: requestReducer(
      actions.GET_BOOKING_AVAILABILITY_REQUEST,
      actions.GET_BOOKING_AVAILABILITY_SUCCESS,
      actions.GET_BOOKING_AVAILABILITY_ERROR
    ),
    relatedEvents: requestReducer(
      actions.FETCH_RELATED_EVENTS_REQUEST,
      actions.FETCH_RELATED_EVENTS_SUCCESS,
      actions.FETCH_RELATED_EVENTS_ERROR
    ),
  }),
  availability: (state = null, action) => {
    switch (action.type) {
      case actions.RESET_BOOKING_AVAILABILITY:
        return null;
      case actions.SET_BOOKING_AVAILABILITY:
        return {...camelizeKeys(action.data.availability), dateRange: action.data.date_range};
      default:
        return state;
    }
  },
  relatedEvents: (state = [], action) => {
    switch (action.type) {
      case actions.RELATED_EVENTS_RECEIVED:
        return camelizeKeys(action.data);
      case actions.RESET_RELATED_EVENTS:
        return [];
      default:
        return state;
    }
  },
});

export default roomSearchReducerFactory('bookRoom', {
  timeline: timelineReducer,
  unavailableRooms: unavailableReducer,
  suggestions: suggestionsReducer,
  bookingForm: bookingFormReducer,
});
