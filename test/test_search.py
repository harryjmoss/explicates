# -*- coding: utf8 -*-

import json
from nose.tools import *
from base import Test, db, with_context
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.sql import and_
from datetime import datetime, timedelta

from factories import AnnotationFactory
from explicates.search import Search


class TestSearch(Test):

    def setUp(self):
        super(TestSearch, self).setUp()
        self.search = Search(db)

    def test_collection_clause(self):
        """Test collection clause."""
        iri = 'foo'
        clause = self.search._get_collection_clause(iri)
        assert_equal(str(clause), 'collection.id = :id_1')

    @with_context
    def test_search_by_collection(self):
        """Test search by collection."""
        anno = AnnotationFactory()
        AnnotationFactory()
        collection_iri = anno.collection.id
        results = self.search.search(collection=collection_iri)
        assert_equal(results, [anno])

    def test_contains_clause(self):
        """Test contains clause."""
        data = '{"foo": "bar"}'
        clause = self.search._get_contains_clause(data)
        assert_equal(str(clause), 'annotation._data @> :_data_1')

    def test_contains_clause_with_invalid_json(self):
        """Test get contains with invalid JSON."""
        data = '{""}'
        assert_raises(ValueError, self.search._get_contains_clause, data)

    @with_context
    def test_search_by_contains(self):
        """Test search by contains."""
        data = {'foo': 'bar'}
        anno = AnnotationFactory(data=data)
        AnnotationFactory(data={'baz': 'qux'})
        results = self.search.search(contains=data)
        assert_equal(results, [anno])

    @with_context
    def test_search_by_collection_and_contains(self):
        """Test search by collection and contains."""
        data = {'foo': 'bar'}
        anno = AnnotationFactory(data=data)
        AnnotationFactory(data={'baz': 'qux'})
        collection_iri = anno.collection.id
        results = self.search.search(collection=collection_iri, contains=data)
        assert_equal(results, [anno])

    def test_ranges_clause(self):
        """Test range clauses."""
        data = {
            'created': {
                'gte': 'foo',
                'lte': 'foo',
                'gt': 'foo',
                'lt': 'foo'
            }
        }
        clauses = self.search._get_range_clauses(json.dumps(data))
        assert_equal(len(clauses), 4)
        str_clauses = [str(c) for c in clauses]
        for op in ['<', '>', '<=', '>=']:
            assert_in('annotation.created {} :created_1'.format(op),
                      str_clauses)

    def test_range_clauses_with_invalid_settings(self):
        """Test range clauses with invalid settings."""
        data = '{"foo": "bar"}'
        assert_raises(ValueError, self.search._get_range_clauses, data)

    def test_range_clauses_with_invalid_operator(self):
        """Test range clauses with invalid operator."""
        data = '{"created": {"foo": "bar"}}'
        assert_raises(ValueError, self.search._get_range_clauses, data)

    def test_range_clauses_with_invalid_json(self):
        """Test range clauses with invalid JSON."""
        data = '{""}'
        assert_raises(ValueError, self.search._get_range_clauses, data)

    @with_context
    def test_search_by_range_lt(self):
        """Test search by range less than."""
        anno_now = AnnotationFactory()
        now = datetime.utcnow()
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        anno_yesterday = AnnotationFactory(created=yesterday)
        AnnotationFactory()
        range_query = {
            'created': {
                'lt': anno_now.created
            }
        }
        results = self.search.search(range=range_query)
        assert_equal(results, [anno_yesterday])

    @with_context
    def test_search_by_range_gt(self):
        """Test search by range greater than."""
        anno = AnnotationFactory(data={'body': 43})
        AnnotationFactory()
        range_query = {
            'body': {
                'gt': 42
            }
        }
        results = self.search.search(range=range_query)
        assert_equal(results, [anno])

    def test_fts_clauses_with_invalid_json(self):
        """Test fts clauses with invalid JSON."""
        data = '{""}'
        assert_raises(ValueError, self.search._get_fts_clauses, data)

    def test_fts_clauses_with_invalid_settings(self):
        """Test fts clauses with invalid settings."""
        data = '{"foo": "bar"}'
        assert_raises(ValueError, self.search._get_fts_clauses, data)

    def test_fts_clauses_with_missing_query(self):
        """Test fts clauses with invalid settings."""
        data = '{"foo": {"bar":"baz"}}'
        assert_raises(ValueError, self.search._get_fts_clauses, data)

    @with_context
    def test_search_by_fts_default(self):
        """Test search by fts with default settings."""
        anno1 = AnnotationFactory(data={'body': {'source': 'foo'}})
        anno2 = AnnotationFactory(data={'body': 'bar'})
        fts_query = {
            'body': {
                'query': 'fo'
            }
        }
        results = self.search.search(fts=fts_query)
        assert_equal(results, [anno1])

    @with_context
    def test_search_by_fts_different_case(self):
        """Test search by fts with different case."""
        anno1 = AnnotationFactory(data={'body': {'source': 'FOO'}})
        anno2 = AnnotationFactory(data={'body': 'bar'})
        fts_query = {
            'body': {
                'query': 'fo'
            }
        }
        results = self.search.search(fts=fts_query)
        assert_equal(results, [anno1])

    @with_context
    def test_search_by_fts_does_not_include_keys(self):
        """Test search by fts does not include keys."""
        anno1 = AnnotationFactory(data={'body': {'source': 'foo'}})
        fts_query = {
            'body': {
                'query': 'source'
            }
        }
        results = self.search.search(fts=fts_query)
        assert_equal(results, [])

    @with_context
    def test_search_by_fts_without_prefix(self):
        """Test search by fts without prefix."""
        anno1 = AnnotationFactory(data={'body': 'qux'})
        AnnotationFactory(data={'body': 'quxx'})
        fts_query = {
            'body': {
                'query': 'qux',
                'prefix': False
            }
        }
        results = self.search.search(fts=fts_query)
        assert_equal(results, [anno1])

    @with_context
    def test_search_by_fts_default_with_or(self):
        """Test search by fts with default settings with or."""
        anno1 = AnnotationFactory(data={'body': {'source': 'foo'}})
        anno2 = AnnotationFactory(data={'body': 'bar'})
        anno3 = AnnotationFactory(data={'body': 'baz'})
        fts_query = {
            'body': {
                'query': 'foo bar',
                'operator': 'or'
            }
        }
        results = self.search.search(fts=fts_query)
        assert_equal(results, [anno1, anno2])

    def test_fts_phrase_clauses_with_invalid_settings(self):
        """Test fts phrase clauses with invalid settings."""
        data = '{"foo": "bar"}'
        assert_raises(ValueError, self.search._get_fts_phrase_clauses, data)

    def test_fts_phrase_clauses_with_missing_query(self):
        """Test fts phrase clauses with invalid settings."""
        data = '{"foo": {"bar":"baz"}}'
        assert_raises(ValueError, self.search._get_fts_phrase_clauses, data)

    @with_context
    def test_search_by_fts_phrase(self):
        """Test search by fts phrase."""
        anno1 = AnnotationFactory(data={'body': {'source': 'foo bar baz'}})
        anno2 = AnnotationFactory(data={'body': 'foo bar baz qux'})
        AnnotationFactory(data={'body': 'foo baz'})
        fts_phrase_query = {
            'body': {
                'query': 'foo bar baz'
            }
        }
        results = self.search.search(fts_phrase=fts_phrase_query)
        assert_equal(results, [anno1, anno2])

    @with_context
    def test_search_by_fts_phrase_with_distance(self):
        """Test search by fts phrase with distance."""
        anno1 = AnnotationFactory(data={'body': 'foo bar baz qux'})
        AnnotationFactory(data={'body': 'foo bar qux'})
        AnnotationFactory(data={'body': 'foo qux'})
        fts_phrase_query = {
            'body': {
                'query': 'foo qux',
                'distance': 3
            }
        }
        results = self.search.search(fts_phrase=fts_phrase_query)
        assert_equal(results, [anno1])

    def test_collection_clause(self):
        """Test collection clause."""
        iri = 'foo'
        clause = self.search._get_collection_clause(iri)
        assert_equal(str(clause), 'collection.id = :id_1')

    @with_context
    def test_search_excludes_deleted_annotations_by_default(self):
        """Test search excludes deleted Annotations by default."""
        anno = AnnotationFactory()
        AnnotationFactory(deleted=True)
        results = self.search.search()
        assert_equal(results, [anno])

    @with_context
    def test_search_excludes_deleted_annotations_explicitly(self):
        """Test search excludes deleted Annotations explicitly."""
        anno = AnnotationFactory()
        AnnotationFactory(deleted=True)
        results = self.search.search(deleted='exclude')
        assert_equal(results, [anno])

    @with_context
    def test_search_includes_deleted_annotations(self):
        """Test search includes deleted Annotations."""
        anno1 = AnnotationFactory()
        anno2 = AnnotationFactory(deleted=True)
        results = self.search.search(deleted='include')
        assert_equal(results, [anno1, anno2])

    @with_context
    def test_search_returns_only_deleted_annotations(self):
        """Test search returns only deleted Annotations."""
        anno = AnnotationFactory(deleted=True)
        AnnotationFactory()
        results = self.search.search(deleted='only')
        assert_equal(results, [anno])

    @with_context
    def test_search_raises_when_invalid_deleted_value(self):
        """Test search raises ValueError with invalid deleted argumement."""
        assert_raises(ValueError, self.search._get_deleted_clause, 'foo')

    @with_context
    def test_offset(self):
        """Test search with offset."""
        size = 5
        offset = 2
        annotations = AnnotationFactory.create_batch(size)
        results = self.search.search(offset=offset)
        assert_equal(len(results), size - offset)
