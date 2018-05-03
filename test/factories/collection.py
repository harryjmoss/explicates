# -*- coding: utf8 -*-

from pywa.model.collection import Collection
from . import BaseFactory, factory, collection_repo


class CollectionFactory(BaseFactory):
    class Meta:
        model = Collection

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        collection = model_class(*args, **kwargs)
        collection_repo.save(task)
        return collection

    id = factory.Sequence(lambda n: n)