# -*- coding: utf-8 -*-
"""Sync behaviors."""


from Acquisition import aq_base
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from collective.contentsync import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer.decorator import indexer
from plone.supermodel import model
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


def context_property(name, default=None):
    def getter(self, default=default):
        return getattr(aq_base(self.context), name, default)

    def setter(self, value):
        setattr(self.context, name, value)

    def deleter(self):
        delattr(self.context, name)

    return property(getter, setter, deleter)


class ISyncSettingRow(model.Schema):
    """A dedicated sync configuration."""

    sync_target = schema.Choice(
        description=_(u"Please select one target from the list."),
        required=True,
        title=_(u"Sync Target"),
        vocabulary="collective.contentsync.targets",
    )

    sync_enabled = schema.Bool(
        default=False,
        description=_(
            "When activated synchronization will be active. Note that there must be "
            u"a corresponding content rule available executing the ”Sync content” "
            u"action.",
        ),
        required=False,
        title=_("Enable content sync"),
    )

    sync_target_path = schema.TextLine(
        required=True,
        title=_(u"Target path"),
    )

    sync_include_subcontent = schema.Bool(
        default=False,
        description=_("When activated sub content will be synchronized as well."),
        required=False,
        title=_("Sync sub content"),
    )


@provider(IFormFieldProvider)
class ISyncSettings(model.Schema):
    """Configure content syncing."""

    model.fieldset(
        "collective.contentsync",
        label=_("Content Sync"),
        fields=[
            "sync_disabled",
            "sync_settings",
        ],
    )

    sync_disabled = schema.Bool(
        default=False,
        description=_(
            "When activated synchronization of sub content will stop at this "
            u"content item for all sync targets.",
        ),
        required=False,
        title=_("Exclude item from content sync"),
    )

    directives.widget(sync_settings=DataGridFieldFactory)
    sync_settings = schema.List(
        default=[],
        required=False,
        title=_("Sync Settings"),
        value_type=DictRow(title=_("Sync Setting"), schema=ISyncSettingRow),
    )


@implementer(ISyncSettings)
@adapter(IDexterityContent)
class SyncSettings(object):
    """Adapter for ISyncSettings."""

    def __init__(self, context):
        self.context = context

    sync_disabled = context_property("sync_disabled")
    sync_settings = context_property("sync_settings")


@indexer(IDexterityContent)
def has_sync_enabled(obj):
    try:
        adapter = ISyncSettings(obj)
    except TypeError:
        return
    else:
        for setting in adapter.sync_settings:
            if setting.get("sync_enabled", False):
                return True
        return False
