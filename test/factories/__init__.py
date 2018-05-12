# -*- coding: utf8 -*-

import factory

from explicates.core import db
from explicates.repositories import AnnotationRepository
from explicates.repositories import CollectionRepository
from explicates.model.annotation import Annotation
from explicates.model.collection import Collection


annotation_repo = AnnotationRepository(db, Annotation)
collection_repo = CollectionRepository(db, Collection)


def reset_all_pk_sequences():
    AnnotationFactory.reset_sequence()
    CollectionFactory.reset_sequence()


class BaseFactory(factory.Factory):
    @classmethod
    def _setup_next_sequence(cls):
        return 1

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        item = model_class(*args, **kwargs)
        db.session.remove()
        return item


# Import the factories
from annotation import AnnotationFactory
from collection import CollectionFactory
