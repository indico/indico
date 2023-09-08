# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.contributions import Contribution
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.editing.models.editable import Editable
from indico.modules.events.editing.models.revisions import EditingRevision
from indico.modules.events.papers.models.revisions import PaperRevision
from indico.modules.events.registration.models.registrations import Registration, RegistrationData


def get_registration_data(user):
    """Get all files uploaded in registration file fields."""
    return (RegistrationData.query
            .join(Registration)
            .filter(Registration.user == user,
                    RegistrationData.filename.isnot(None))
            .all())


def get_attachments(user):
    """Get all attachments uploaded by the user."""
    return Attachment.query.filter(Attachment.user == user, Attachment.type == AttachmentType.file).all()


def get_contributions(user):
    """Get all contributions linked to the user (author, speaker or submitter)."""
    return (Contribution.query.options(joinedload('person_links'))
            .filter(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)))
            .all())


def get_subcontributions(user):
    """Get all subcontributions linked to the user (speaker)."""
    return (SubContribution.query
            .options(joinedload('person_links'))
            .filter(SubContribution.person_links.any(SubContributionPersonLink.person.has(user=user)))
            .all())


def get_abstracts(user):
    """Get all abstracts where the user is either the submitter or is linked to the abstract."""
    return (Abstract.query.options(joinedload('person_links'))
            .filter(db.or_(Abstract.submitter == user,
                           Abstract.person_links.any(AbstractPersonLink.person.has(user=user))))
            .all())


def get_papers(user):
    """Get all papers where the user is either linked to the parent contribution or has submitted a paper revision."""
    contribs = (Contribution.query.options(joinedload('person_links'))
                .filter(db.or_(db.and_(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)),
                                       Contribution._paper_revisions.any()),
                               Contribution._paper_revisions.any(PaperRevision.submitter == user)))
                .all())
    return [contrib.paper for contrib in contribs]


def get_editables(user):
    """
    Get all editables where the user is either linked to the parent contribution or has submitted an editing revision.
    """
    return (Editable.query
            .join(Contribution, Contribution.id == Editable.contribution_id)
            .outerjoin(ContributionPersonLink, ContributionPersonLink.contribution_id == Contribution.id)
            .outerjoin(EditingRevision, EditingRevision.editable_id == Editable.id)
            .filter(db.or_(Contribution.person_links.any(ContributionPersonLink.person.has(user=user)),
                           EditingRevision.user == user))
            .all())
