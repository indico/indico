// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationParentURL from 'indico-url:contributions.api_contribs_location_parent';
import breakCreateURL from 'indico-url:timetable.tt_break_create';

import _ from 'lodash';
import React, {useEffect, useState} from 'react';
import {Field} from 'react-final-form';
import {Button, Dimmer, Loader} from 'semantic-ui-react';

import {
    FinalLocationField,
    FinalSessionColorPicker,
} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

interface BreakFormProps {
    eventId: number;
    locationParent?: Record<string, any>;
    onSubmit: (formData: any) => void;
    initialValues: Record<string, any>;
    loading: boolean;
    [key: string]: any; // Allow additional props
}

interface BreakFormFieldsProps {
    eventId: number;
    locationParent?: LocationParentObj;
    initialValues: Record<string, any>;
    extraOptions?: Record<string, any>;
    hasParent?: boolean;
    [key: string]: any; // Allow additional props
}

export function BreakFormFields({
    locationParent = {inheriting: false},
    initialValues = {},
    extraOptions = {},
    hasParent = false,
}: BreakFormFieldsProps) {
    const {minStartDt, maxEndDt} = extraOptions;

    return (
        <>
            <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
            <FinalTextArea name="description" label={Translate.string('Description')} />
            {initialValues.start_dt ? (
                <>
                    <Field name="duration" subscription={{value: true}}>
                        {() => (
                            <FinalDateTimePicker
                                name="start_dt"
                                label={Translate.string('Start time')}
                                required
                                minStartDt={minStartDt}
                                maxEndDt={maxEndDt}
                            />
                        )}
                    </Field>
                    <Field name="start_dt" subscription={{value: true}}>
                        {() => (
                            <FinalDuration
                                name="duration"
                                label={Translate.string('Duration')}
                            />
                        )}
                    </Field>
                </>
            ) : (
                <FinalDuration name="duration" label={Translate.string('Duration')} />
            )}
            <FinalLocationField
                name="location_data"
                label={Translate.string('Location')}
                locationParent={locationParent}
            />
            {!hasParent && <FinalSessionColorPicker name="colors" label={Translate.string('Color')} />}
        </>
    );
}

export function BreakForm({
    eventId,
    locationParent = {},
    onSubmit,
    initialValues = {},
    loading,
    ...rest
}: BreakFormProps) {
    const handleSubmit = (formData: any) => {
        onSubmit(formData);
    };

    if (loading) {
        return (
            <Dimmer active>
                <Loader />
            </Dimmer>
        );
    }

    return (
        <FinalModalForm
            id="break-form"
            onSubmit={handleSubmit}
            initialValues={initialValues}
            size="small"
            {...rest}
        >
            <BreakFormFields {...{locationParent, initialValues}} />
        </FinalModalForm>
    );
}

export function BreakEditForm({eventId, breakId, onClose}: {eventId: number; breakId: number; onClose: () => void}) {
    const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
        locationParentURL({event_id: eventId, break_id: breakId})
    );
    const breakURL = breakURL(snakifyKeys({eventId, breakId}));
    const {data: breakData, loading: breakLoading} = useIndicoAxios(breakURL);

    const handleSubmit = async (formData: any) => {
        try {
            await indicoAxios.patch(breakURL, formData);
        } catch (e) {
            return handleSubmitError(e);
        }
        location.reload();
        // never finish submitting to avoid fields being re-enabled
        await new Promise(() => {});
    };

    const loading = breakLoading || locationParentLoading;

    return (
        <BreakForm
            eventId={eventId}
            locationParent={locationParent}
            header={Translate.string("Edit break '{title}'", {title: breakData?.title})}
            onSubmit={handleSubmit}
            onClose={onClose}
            initialValues={loading ? {} : breakData}
            loading={loading}
        />
    );
}

export function BreakCreateForm({
    eventId,
    onClose,
    customInitialValues = {},
}: {
    eventId: number;
    onClose: () => void;
    customInitialValues?: Record<string, any>;
}) {
    const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
        locationParentURL({event_id: eventId})
    );

    const handleSubmit = async (formData: any) => {
        try {
            await indicoAxios.post(breakCreateURL({event_id: eventId}), formData);
        } catch (e) {
            return handleSubmitError(e);
        }
        location.reload();
        // never finish submitting to avoid fields being re-enabled
        await new Promise(() => {});
    };

    const locationData = locationParent
        ? {...locationParent.location_data, inheriting: true}
        : {inheriting: false};
    const loading = locationParentLoading;

    const initialValues = loading
        ? {}
        : {
                duration: '',
                location_data: locationData,
                ...customInitialValues,
            };

    return (
        <BreakForm
            eventId={eventId}
            locationParent={locationParent}
            header={Translate.string('Add new break')}
            onSubmit={handleSubmit}
            onClose={onClose}
            initialValues={initialValues}
            loading={loading}
        />
    );
}

export function EditBreakButton({eventId, breakId, eventTitle, triggerSelector, ...rest}: {
    eventId: number;
    breakId: number;
    eventTitle: string;
    triggerSelector?: string;
}) {
    const [open, setOpen] = useState(false);

    useEffect(() => {
        if (!triggerSelector) {
            return;
        }
        const handler = () => setOpen(true);
        const element = document.querySelector(triggerSelector);
        element.addEventListener('click', handler);
        return () => element.removeEventListener('click', handler);
    }, [triggerSelector]);

    return (
        <>
            {!triggerSelector && (
                <Button onClick={() => setOpen(true)} {...rest}>
                    <Translate>Edit break</Translate>
                </Button>
            )}
            {open && (
                <BreakEditForm
                    eventId={eventId}
                    breakId={breakId}
                    eventTitle={eventTitle}
                    onClose={() => setOpen(false)}
                />
            )}
        </>
    );
}

export function CreateBreakButton({eventId, triggerSelector, ...rest}: {
    eventId: number;
    triggerSelector?: string;
}) {
    const [open, setOpen] = useState(false);

    useEffect(() => {
        if (!triggerSelector) {
            return;
        }
        const handler = () => setOpen(true);
        const element = document.querySelector(triggerSelector);
        element.addEventListener('click', handler);
        return () => element.removeEventListener('click', handler);
    }, [triggerSelector]);

    return (
        <>
            {!triggerSelector && (
                <Button onClick={() => setOpen(true)} {...rest}>
                    <Translate>Create break</Translate>
                </Button>
            )}
            {open && (
                <BreakCreateForm
                    eventId={eventId}
                    onClose={() => setOpen(false)}
                    customInitialValues={{}}
                />
            )}
        </>
    );
}
