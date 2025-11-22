// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import adminAffiliationURL from 'indico-url:users.api_admin_affiliation';
import adminAffiliationsURL from 'indico-url:users.api_admin_affiliations';

import type {FormApi} from 'final-form';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

import AffiliationFormModal from './AffiliationFormModal';
import {AffiliationFormValues} from './types';

interface AffiliationFormDialogProps {
  trigger: React.ReactElement;
  affiliationId?: number;
  onSuccess: (data: Record<string, unknown>) => void;
}

export default function AffiliationFormDialog({
  trigger,
  affiliationId,
  onSuccess,
}: AffiliationFormDialogProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [initialValues, setInitialValues] = useState<Partial<AffiliationFormValues> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isEdit = typeof affiliationId === 'number';

  const closeDialog = useCallback(() => {
    setIsOpen(false);
    setInitialValues(null);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (!isOpen || !isEdit) {
      return;
    }
    let active = true;
    const load = async () => {
      setIsLoading(true);
      try {
        const response = await indicoAxios.get(
          adminAffiliationURL({affiliation_id: affiliationId})
        );
        if (active) {
          setInitialValues(camelizeKeys(response.data));
        }
      } catch (error) {
        if (active) {
          handleAxiosError(error);
          closeDialog();
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [affiliationId, closeDialog, isEdit, isOpen]);

  const handleTriggerClick = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      if (trigger.props.onClick) {
        trigger.props.onClick(event);
      }
      if (event.defaultPrevented || trigger.props.disabled) {
        return;
      }
      setInitialValues(null);
      setIsOpen(true);
      if (!isEdit) {
        setIsLoading(false);
      }
    },
    [isEdit, trigger]
  );

  const clonedTrigger = useMemo(
    () => React.cloneElement(trigger, {onClick: handleTriggerClick}),
    [trigger, handleTriggerClick]
  );

  const handleSubmit = useCallback(
    async (formData: AffiliationFormValues, form: FormApi<AffiliationFormValues>) => {
      try {
        const payload = snakifyKeys(isEdit ? getChangedValues(formData, form) : formData);
        let response;
        if (isEdit) {
          response = await indicoAxios.patch(
            adminAffiliationURL({affiliation_id: affiliationId}),
            payload
          );
        } else {
          response = await indicoAxios.post(adminAffiliationsURL({}), payload);
        }
        onSuccess(camelizeKeys(response.data));
        closeDialog();
      } catch (error) {
        return handleSubmitError(error);
      }
    },
    [affiliationId, closeDialog, isEdit, onSuccess]
  );

  return (
    <>
      {clonedTrigger}
      {isOpen && (
        <AffiliationFormModal
          mode={isEdit ? 'edit' : 'create'}
          initialValues={initialValues || undefined}
          onClose={closeDialog}
          onSubmit={handleSubmit}
          loading={isEdit && (isLoading || !initialValues)}
        />
      )}
    </>
  );
}
