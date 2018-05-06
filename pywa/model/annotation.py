# -*- coding: utf8 -*-

import urllib
from flask import current_app, url_for
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy import Integer, Text, Unicode
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from pywa.core import db
from pywa.model import make_timestamp, make_uuid
from pywa.model.base import BaseDomainObject
from pywa.model.collection import Collection

try:
    from urllib import quote
except ImportError:  # py3
    from urllib.parse import quote


class Annotation(db.Model, BaseDomainObject):
    """An annotation"""

    __tablename__ = 'annotation'

    #: The Annotation primary key.
    key = Column(Integer, primary_key=True)

    #: The IRI path segement appended to the Annotation IRI.
    slug = Column(Unicode(), unique=True, default=unicode(make_uuid()))

    #: The relationship between the Annotation and its Body.
    body = Column(JSONB, nullable=False)

    #: The relationship between the Annotation and its Target.
    target = Column(JSONB, nullable=False)

    #: The time at which the Annotation was created.
    created = Column(Text, default=make_timestamp)

    #: The agent responsible for creating the Annotation.
    creator = Column(JSONB)

    #: The time at which the Annotation was modified, after creation.
    modified = Column(Text)

    #: The relationship between the Annotation and the Style.
    stylesheet = Column(JSONB)

    #: The related Collection ID.
    collection_key = Column(Integer, ForeignKey('collection.key'),
                            nullable=False)

    #: The related Collection.
    collection = relationship(Collection)

    @hybrid_property
    def id(self):
        root_url = url_for('api.index')
        collection_slug = quote(self.collection.slug.encode('utf8'))
        annotation_slug = quote(self.slug.encode('utf8'))
        return '{}{}/{}'.format(root_url, collection_slug, annotation_slug)

    @hybrid_property
    def type(self):
        return 'Annotation'

    @hybrid_property
    def generator(self):
        return current_app.config.get('GENERATOR')

    @hybrid_property
    def generated(self):
        return make_timestamp()

    @validates('body')
    def validate_body(self, key, body):
        self.validate_json(key, body, 'annotation_body.json')
        return body

    @validates('target')
    def validate_target(self, key, target):
        self.validate_json(key, target, 'annotation_target.json')
        return target
