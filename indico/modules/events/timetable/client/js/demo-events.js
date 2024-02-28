// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

const colors = [
  {text: '#1D041F', background: '#EEE0EF'},
  {text: '#253F08', background: '#E3F2D3'},
  {text: '#1F1F02', background: '#FEFFBF'},
  {text: '#202020', background: '#DFE555'},
  {text: '#1F1D04', background: '#FFEC1F'},
  {text: '#0F264F', background: '#DFEBFF'},
  {text: '#EFF5FF', background: '#0D316F'},
  {text: '#F1FFEF', background: '#1A3F14'},
  {text: '#FFFFFF', background: '#5F171A'},
  {text: '#272F09', background: '#D9DFC3'},
  {text: '#FFEFFF', background: '#4F144E'},
  {text: '#FFEDDF', background: '#6F390D'},
  {text: '#021F03', background: '#8EC473'},
  {text: '#03070F', background: '#92B6DB'},
  {text: '#151515', background: '#DFDFDF'},
  {text: '#1F1100', background: '#ECC495'},
  {text: '#0F0202', background: '#B9CBCA'},
  {text: '#0D1E1F', background: '#C2ECEF'},
  {text: '#000000', background: '#D0C296'},
  {text: '#202020', background: '#EFEBC2'},
];

const randomColor = () => colors[Math.floor(Math.random() * colors.length)];

export default [
  {
    id: 0,
    title: 'Meeting',
    start: new Date(2024, 3, 1, 10, 30, 0, 0),
    end: new Date(2024, 3, 1, 12, 30, 0, 0),
    desc: 'Pre-meeting meeting, to prepare for the meeting',
    color: randomColor(),
  },
  {
    id: 1,
    title: 'Lunch',
    start: new Date(2024, 3, 1, 12, 0, 0, 0),
    end: new Date(2024, 3, 1, 13, 0, 0, 0),
    desc: 'Power lunch',
    color: randomColor(),
  },
  {
    id: 2,
    title: 'Meeting',
    start: new Date(2024, 3, 1, 14, 0, 0, 0),
    end: new Date(2024, 3, 1, 15, 0, 0, 0),
    color: randomColor(),
  },
  {
    id: 3,
    title: 'Happy Hour',
    start: new Date(2024, 3, 1, 17, 0, 0, 0),
    end: new Date(2024, 3, 1, 17, 30, 0, 0),
    desc: 'Most important meal of the day',
    color: randomColor(),
  },
  {
    id: 4,
    title: 'Dinner',
    start: new Date(2024, 3, 1, 20, 0, 0, 0),
    end: new Date(2024, 3, 1, 21, 0, 0, 0),
    color: randomColor(),
  },
  {
    id: 5,
    title: 'Session Block 1',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 10, 30, 0),
    color: randomColor(),
  },
  {
    id: 6,
    title: 'Session Block 2',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 10, 30, 0),
    color: randomColor(),
  },
  {
    id: 7,
    title: 'Session Block 3',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 10, 30, 0),
    color: randomColor(),
  },
  {
    id: 8,
    title: 'Contribution 1.1',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 10, 30, 0),
    parent: 5,
  },
  {
    id: 9,
    title: 'Contribution 1.2',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 10, 30, 0),
    parent: 5,
  },
  {
    id: 10,
    title: 'Contribution 2.1',
    start: new Date(2024, 3, 1, 7, 0, 0),
    end: new Date(2024, 3, 1, 8, 0, 0),
    parent: 6,
  },
  {
    id: 11,
    title: 'Contribution 2.2',
    start: new Date(2024, 3, 1, 8, 0, 0),
    end: new Date(2024, 3, 1, 9, 0, 0),
    parent: 6,
  },
];
