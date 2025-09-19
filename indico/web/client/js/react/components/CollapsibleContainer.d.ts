// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {ComponentType} from 'react';

interface CollapsibleContainerProps {
  title: string;
  titleSize?: 'tiny' | 'small' | 'medium' | 'large' | 'huge';
  defaultOpen?: boolean;
  styled?: boolean;
  dividing?: boolean;
  children: React.ReactNode;
}

declare const CollapsibleContainer: ComponentType<CollapsibleContainerProps>;

export default CollapsibleContainer;
