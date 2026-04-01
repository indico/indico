# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import abc
import dataclasses

import ollama
from indico_ror.models.affiliation_vs_document import AffiliationVectorStoreDocument
from langchain_ollama import OllamaEmbeddings
from sqlalchemy import delete, literal, select, union_all

from indico.core.db import db
from indico.core.logger import Logger


logger = Logger.get('affiliations')


def is_model_pulled(model_name: str) -> bool:
    models = ollama.list()
    return any(model.model.split(':')[0] == model_name for model in models.models)


def ensure_model(model_name: str):
    """Pull a model if it's not already available."""
    if not is_model_pulled(model_name):
        # ollama.pull downloads from some remote archive; we should instead pre-fetch whichever
        # models we actually need
        logger.warning('downloading external model %r - this should be removed in production', model_name)
        logger.info('model %r not found locally, pulling...', model_name)
        ollama.pull(model_name)
        logger.info('model %r pulled successfully', model_name)


@dataclasses.dataclass(frozen=True)
class AffiliationSearchMatch:
    score: float
    text: str
    affiliation_id: int


class AffiliationSearch(abc.ABC):
    @abc.abstractmethod
    def init(self, texts: list[str], affiliation_ids: list[int]) -> list[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def add(self, texts: list[str], affiliation_ids: list[int]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, texts: list[str], affiliation_ids: list[int], changed_affiliations: list[int]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, affiliation_ids: list[int]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def match_many(self, texts: list[str], k: int = 1) -> list[list[AffiliationSearchMatch]]:
        raise NotImplementedError

    @abc.abstractmethod
    def match(self, text: str, k: int = 1) -> list[AffiliationSearchMatch]:
        raise NotImplementedError


class PSQLVectorStoreBackedAffiliationSearch(AffiliationSearch):
    def __init__(
         self, model: str = 'jina/jina-embeddings-v2-small-en', batch_size: int = 512, threshold: float = 0.3
    ) -> None:
        ensure_model(model)
        self.model = model
        self.embeddings = OllamaEmbeddings(
            model=model,
        )
        self.batch_size = batch_size
        self.threshold = threshold

    @staticmethod
    def cosine_distance_to_score(distance: float) -> float:
        return 1 - distance

    def init(self, texts: list[str], affiliation_ids: list[int]) -> list[str]:
        return self.add(texts, affiliation_ids)

    def add(self, texts: list[str], affiliation_ids: list[int]) -> None:
        if len(texts) == 0:
            return
        for i in range(0, len(texts), self.batch_size):
            embeddings = self.embeddings.embed_documents(texts[i:i+self.batch_size])
            for j in range(len(embeddings)):
                db.session.add(AffiliationVectorStoreDocument(
                    content=texts[i+j],
                    embedding=embeddings[j],
                    affiliation_id=affiliation_ids[i+j],
                ))
            db.session.flush()
        db.session.flush()

    def update(self, texts: list[str], affiliation_ids: list[int], changed_affiliations: list[int]) -> None:
        if len(texts) == 0:
            return
        self.delete(changed_affiliations)
        return self.add(texts, affiliation_ids)

    def delete(self, affiliation_ids: list[int]) -> None:
        if len(affiliation_ids) == 0:
            return
        db.session.execute(
            delete(AffiliationVectorStoreDocument)
            .where(AffiliationVectorStoreDocument.affiliation_id.in_(affiliation_ids))
        )

    def match_embeddings(
        self, embeddings: list[list[float]], k: int = 1
    ) -> list[list[AffiliationSearchMatch]]:
        subqueries = []
        for i, embedding in enumerate(embeddings):
            distance = AffiliationVectorStoreDocument.embedding.cosine_distance(embedding).label('distance')
            subqueries.append(
                select(
                    literal(i).label('embedding_index'),
                    AffiliationVectorStoreDocument.id.label('id'),
                    distance
                ).where(distance < self.threshold)
                .order_by(distance)
                .limit(k)
            )
        combined = union_all(*subqueries).subquery()

        results = db.session.execute(
            select(
                combined.c.embedding_index,
                AffiliationVectorStoreDocument,
                combined.c.distance
            )
            .join(AffiliationVectorStoreDocument, AffiliationVectorStoreDocument.id == combined.c.id)
            .order_by(combined.c.embedding_index, combined.c.distance)
        ).all()

        grouped: dict[int, list[AffiliationSearchMatch]] = {i: [] for i in range(len(embeddings))}
        for embedding_index, doc, dist in results:
            grouped[embedding_index].append(AffiliationSearchMatch(
                score=self.cosine_distance_to_score(dist), text=doc.content, affiliation_id=doc.affiliation_id
            ))

        return [grouped[i] for i in sorted(grouped.keys())]

    def match_embedding(self, embedding: list[float], k: int = 1) -> list[AffiliationSearchMatch]:
        distance = AffiliationVectorStoreDocument.embedding.cosine_distance(embedding).label('distance')
        return [
            AffiliationSearchMatch(
                score=self.cosine_distance_to_score(dist), text=doc.content, affiliation_id=doc.affiliation_id
            )
            for doc, dist in db.session.execute(
                select(AffiliationVectorStoreDocument, distance)
                .where(distance < self.threshold)
                .order_by(distance)
                .limit(k)
            ).all()
        ]

    def match_many(self, texts: list[str], k: int = 1) -> list[list[AffiliationSearchMatch]]:
        return self.match_embeddings([self.embeddings.embed_query(text) for text in texts], k)

    def match(self, text: str, k: int = 1) -> list[AffiliationSearchMatch]:
        return self.match_embedding(self.embeddings.embed_query(text), k)
