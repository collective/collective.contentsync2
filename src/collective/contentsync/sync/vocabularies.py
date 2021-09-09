# -*- coding: utf-8 -*-
"""Sync related vocabularies."""

from collective.contentsync import _
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

import plone.api


@implementer(IVocabularyFactory)
class SyncTargetsVocabulary(object):
    """Return a list of available sync targets."""
    def _get_registry_record(self, iface=None, name=None):
        try:
            return plone.api.portal.get_registry_record(name=name,
                                                        interface=iface)
        except plone.api.exc.InvalidParameterError:
            return []
        except KeyError:
            registry = getUtility(IRegistry)
            registry.registerInterface(iface)
            try:
                return plone.api.portal.get_registry_record(name=name,
                                                            interface=iface)
            except (KeyError, plone.api.exc.InvalidParameterError):
                plone.api.portal.show_message(
                    message=_(
                        u"Please upgrade or reinstall collective.contentsync"),
                    request=getRequest(),
                )
                return []

    def __call__(self, context):
        options = self._get_registry_record(
            name="collective.contentsync.targets")
        items = []

        for option in options or ():
            try:
                target_id = option.get('id', '')
                title = option.get('title', '')
            except ValueError:
                continue
            items.append(SimpleTerm(value=target_id, title=title))
        return SimpleVocabulary(items)


SyncTargetsVocabularyFactory = SyncTargetsVocabulary()
