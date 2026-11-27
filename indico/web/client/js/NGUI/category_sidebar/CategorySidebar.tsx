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

const sidebarContentStyle: React.CSSProperties = {
  flexDirection: 'row',
  flexWrap: 'nowrap',
  alignItems: 'center',
  minWidth: 0,
};

export function CategorySidebar({categoryId}: CategorySidebarProps) {
  const {data: managersData, loading: managersLoading} = useIndicoAxios(
    {url: apiCategoryManagersURL({category_id: categoryId})},
    {camelize: true}
  );
  const managers = managersData as CategoryManager[] | null;
  const {data: materialsData, loading: materialsLoading} = useIndicoAxios(
    {url: apiCategoryMaterialsURL({category_id: categoryId})},
    {camelize: true}
  );
  const materials = materialsData as {
    files: CategoryMaterial[];
    folders: CategoryMaterial[];
  } | null;

  if (managersLoading || materialsLoading) {
    return null;
  }

  const managerList = managers ?? [];
  const materialFiles = materials?.files ?? [];
  const materialFolders = materials?.folders ?? [];
  if (!managerList.length && !materialFiles.length && !materialFolders.length) {
    return null;
  }

  return (
    <div styleName="category-sidebar" data-category-sidebar>
      {managerList.length > 0 && (
        <Card>
          <Card.Header styleName="manager-header">
            <Card.Icon icon="fas:folder" />
            <Translate>Managers</Translate>
          </Card.Header>
          <List styleName="sidebar-list">
            {managerList.map(manager => (
              <List.Item key={manager.id} contentProps={{style: sidebarContentStyle}}>
                <img styleName="manager-avatar" src={manager.avatarURL} alt="" />
                <List.Item.Details className="category-sidebar-item-details">
                  {manager.fullName}
                </List.Item.Details>
              </List.Item>
            ))}
          </List>
        </Card>
      )}
      {materialFiles.length > 0 || materialFolders.length > 0 ? (
        <Card>
          <Card.Header styleName="manager-header">
            <Card.Icon icon="fas:paperclip" />
            <Translate>Materials</Translate>
          </Card.Header>
          <div styleName="material-groups">
            {materialFiles.length > 0 && (
              <List styleName="material-list">
                {materialFiles.map(material => (
                  <MaterialItem key={`file-${material.id}`} material={material} />
                ))}
              </List>
            )}
            {materialFolders.map(folder => (
              <div styleName="material-folder-group" key={`folder-${folder.id}`}>
                <List styleName="material-list">
                  <MaterialItem material={folder} isFolder />
                  {folder.attachments?.map(material => (
                    <MaterialItem
                      key={`folder-${folder.id}-file-${material.id}`}
                      material={material}
                      nested
                    />
                  ))}
                </List>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}

interface MaterialItemProps {
  material: CategoryMaterial;
  isFolder?: boolean;
  nested?: boolean;
}

const MATERIAL_EXACT_ICONS: Record<string, string> = {
  'text/calendar': 'fas:calendar',
  'application/msword': 'fas:file-word',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'fas:file-word',
  'application/pdf': 'fas:file-pdf',
  'application/vnd.ms-excel': 'fas:file-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'fas:file-excel',
  'application/vnd.ms-powerpoint': 'fas:file-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation':
    'fas:file-powerpoint',
  'application/x-7z-compressed': 'fas:file-zipper',
  'application/x-ace-compressed': 'fas:file-zipper',
  'application/x-rar-compressed': 'fas:file-zipper',
  'application/x-tar': 'fas:file-zipper',
  'application/zip': 'fas:file-zipper',
  'application/json': 'fas:file-code',
  'text/css': 'fas:file-code',
  'application/xml': 'fas:file-code',
  'text/xml': 'fas:file-code',
  'text/n3': 'fas:file-code',
  'text/html': 'fas:file-code',
  'text/sgml': 'fas:file-code',
  'text/csv': 'fas:table',
  'text/tab-separated-values': 'fas:table',
};

function getMaterialIcon(material: CategoryMaterial): string {
  if (material.type === 'link') {
    return 'fas:link';
  }

  const mimeType = material.contentType?.toLowerCase() ?? '';
  if (MATERIAL_EXACT_ICONS[mimeType]) {
    return MATERIAL_EXACT_ICONS[mimeType];
  }
  if (mimeType.startsWith('application/x-bzip')) {
    return 'fas:file-zipper';
  }
  if (mimeType.includes('vnd.oasis.opendocument')) {
    return 'fas:file-lines';
  }
  if (/(?:[+/](?:xml|json)$)/.test(mimeType)) {
    return 'fas:file-code';
  }

  const prefixIcons: Record<string, string> = {
    'audio/': 'fas:file-audio',
    'image/': 'fas:file-image',
    'text/': 'fas:file-lines',
    'video/': 'fas:file-video',
  };
  const prefix = Object.keys(prefixIcons).find(value => mimeType.startsWith(value));
  if (prefix) {
    return prefixIcons[prefix];
  }
  return 'fas:file';
}

function MaterialItem({material, isFolder = false, nested = false}: MaterialItemProps) {
  const inaccessible = !isFolder && material.isProtected && !material.url;
  const protectionTitle = isFolder
    ? Translate.string('Protected folder')
    : inaccessible
      ? Translate.string('You do not have access to this material')
      : Translate.string('Protected material');
  const contentProps =
    !isFolder && material.url
      ? {
          href: material.url,
          target: '_blank',
          rel: 'noopener noreferrer',
          style: sidebarContentStyle,
        }
      : {style: sidebarContentStyle};
  const styleName = [
    'material',
    isFolder && 'material-folder',
    nested && 'material-nested',
    material.isProtected && 'protected',
    inaccessible && 'inaccessible',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <List.Item
      className="category-sidebar-material-row"
      styleName={styleName}
      contentProps={contentProps}
    >
      <List.Item.Icon
        icon={isFolder ? 'fas:folder' : getMaterialIcon(material)}
        color="gray"
        size="sm"
        variant="transparent"
        compact
      />
      <List.Item.Details className="category-sidebar-item-details" title={material.title}>
        {material.title}
      </List.Item.Details>
      {material.isProtected && (
        <List.Item.Icon
          color="gray"
          icon="fas:lock"
          size="sm"
          variant="transparent"
          compact
          ariaLabel={protectionTitle}
          title={protectionTitle}
        />
      )}
    </List.Item>
  );
}
