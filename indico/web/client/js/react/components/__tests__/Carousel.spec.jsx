// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {fireEvent, render, screen} from '@testing-library/react';
import React from 'react';

import Carousel from '../Carousel';

const panes = [
  {
    key: 'bookings',
    label: 'Your bookings',
    content: <button type="button">Booking details</button>,
  },
  {key: 'statistics', label: 'Statistics', content: <p>Room statistics</p>},
];

test('pane buttons keep the selected content stable and hide the other pane', () => {
  jest.useFakeTimers();
  try {
    render(<Carousel panes={panes} />);

    const bookings = screen.getByRole('button', {name: /current pane.*your bookings/i});
    const statistics = screen.getByRole('button', {name: 'Statistics'});
    expect(screen.getByRole('button', {name: 'Booking details'})).not.toBeNull();
    expect(screen.getByText('Room statistics').closest('[hidden]')).not.toBeNull();

    jest.advanceTimersByTime(21_000);
    expect(bookings.textContent).toContain('Current pane');

    fireEvent.click(statistics);
    expect(screen.getByText('Room statistics').closest('[hidden]')).toBeNull();
    expect(screen.queryByRole('button', {name: 'Booking details'})).toBeNull();
    expect(statistics.textContent).toContain('Current pane');
  } finally {
    jest.useRealTimers();
  }
});
