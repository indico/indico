// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiCategoryManagersURL from 'indico-url:categories.api_category_managers';
import apiCategoryMaterialsURL from 'indico-url:categories.api_category_materials';

import React from 'react';

import './CategorySidebar.module.scss';
import {Card, List} from 'indico/NGUI';
import {CategoryManager, CategoryMaterial} from 'indico/NGUI/types';
import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

interface CategorySidebarProps {
  categoryId: number;
}

export function CategorySidebar({categoryId}: CategorySidebarProps) {
  const {data: managersData, loading: managersLoading} = useIndicoAxios(
    {url: apiCategoryManagersURL({category_id: categoryId})},
    {camelize: true}
  );
  const managers = managersData as CategoryManager[] | undefined;
  const {data: materialsData, loading: materialsLoading} = useIndicoAxios(
    {url: apiCategoryMaterialsURL({category_id: categoryId})},
    {camelize: true}
  );
  const materials = materialsData as
    | {files: CategoryMaterial[]; folders: {attachments: CategoryMaterial[]}[]}
    | undefined;
  const materialItems = materials
    ? [...materials.files, ...materials.folders.flatMap(folder => folder.attachments)]
    : [];

  return (
    <div styleName="category-sidebar">
      {!managersLoading && managers?.length ? (
        <Card>
          <Card.Header styleName="manager-header">
            <Card.Icon icon="fas:folder" />
            <Translate>Managers</Translate>
          </Card.Header>
          <List styleName="sidebar-list">
            {managers.map(manager => (
              <List.Item key={manager.id}>
                <img styleName="manager-avatar" src={manager.avatarURL} alt="" />
                <List.Item.Details>{manager.fullName}</List.Item.Details>
              </List.Item>
            ))}
          </List>
        </Card>
      ) : null}
      {!materialsLoading && materialItems.length ? (
        <Card>
          <Card.Header styleName="manager-header">
            <Card.Icon icon="fas:paperclip" />
            <Translate>Materials</Translate>
          </Card.Header>
          <List styleName="sidebar-list material-list">
            {materialItems.map(material => (
              <List.Item
                key={material.id}
                contentProps={{href: material.url, target: '_blank', rel: 'noopener noreferrer'}}
              >
                <List.Item.Details title={material.title}>{material.title}</List.Item.Details>
              </List.Item>
            ))}
          </List>
        </Card>
      ) : null}
    </div>
  );
}
