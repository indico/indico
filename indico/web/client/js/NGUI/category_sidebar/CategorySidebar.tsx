// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import './CategorySidebar.module.scss';
import {Card} from 'indico/NGUI/card/Card';

export function CategorySidebar() {
  return (
    <div styleName="category-sidebar">
      <Card>
        <Card.Header>
          <Card.Icon icon="fas:folder" />
          Heyyy
        </Card.Header>
        Ajobbb
      </Card>
      <Card>
        <Card.Header>Materials</Card.Header>
        Hello
      </Card>
    </div>
  );
}
