# -*- coding: utf-8 -*-
"""Content rule actions for syncing content."""

from collective.contentsync import _
from collective.contentsync.sync.sync import get_closest_enabled_sync_settings, run_sync
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules.actions import ActionAddForm
from plone.app.contentrules.browser.formhelper import ContentRuleFormWrapper
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapter
from zope.interface import implementer, Interface

import plone.api


class ISyncAction(Interface):
    """Interface for the configurable aspects of a sync action."""


@implementer(ISyncAction, IRuleElementData)
class SyncAction(SimpleItem):
    """The actual persistent implementation of the action element."""

    element = "collective.contentsync.actions.Sync"
    summary = _(u"Sync to an external Plone site")


class SyncAddForm(ActionAddForm):
    """An add form for sync-to-external-Plone-sites actions."""

    schema = ISyncAction
    label = _(u"Add Sync Action")
    description = _(
        u"A sync action can sync an object to a different Plone site.")
    Type = SyncAction


class SyncAddFormView(ContentRuleFormWrapper):
    form = SyncAddForm


@adapter(Interface, ISyncAction, Interface)
@implementer(IExecutable)
class SyncActionExecutor(object):
    """The executor for this action.

    This is registered as an adapter in configure.zcml
    """
    def __init__(self, context, element, event):
        # context is the object where the rule is enabled
        self.context = context
        # element is the action
        self.element = element
        # event contains the event data, including the object
        self.event = event

    def __call__(self):
        adapter = get_closest_enabled_sync_settings(self.event.object)
        if not adapter:
            return False

        sync_now = plone.api.portal.get_registry_record(
            "collective.contentsync.sync_immediately")

        if sync_now:
            try:
                sync_result = run_sync(self.event.object, adapter)
            except Exception:
                sync_result = False

            if sync_result is True:
                return

        # Store in queue for later sync.
        queue = plone.api.portal.get_registry_record(
            "collective.contentsync.queue")
        queue = queue or set()
        path = "/".join(self.event.object.getPhysicalPath())
        if path not in queue:
            queue.add(path)
            plone.api.portal.set_registry_record(
                "collective.contentsync.queue", queue)
        return True
