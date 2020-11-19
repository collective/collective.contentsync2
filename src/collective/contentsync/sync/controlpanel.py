# -*- coding: utf-8 -*-
"""Sync controlpanel view."""

from collective.contentsync import _
from collective.contentsync.sync.sync import full_sync, sync_queue
from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow
from plone.app.registry.browser import controlpanel
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.autoform import directives
from plone.supermodel import model
from plone.z3cform import layout
from z3c.form import button
from z3c.form.browser.multi import MultiWidget
from zope import schema
from zope.interface import implementer, Interface

import plone.api


DEFAULT_OMITTED_UPDATE_FIELDS = []


class ITargetRow(model.Schema):
    target = schema.TextLine(title="Sync target", default='', required=False)


class ISyncControlPanelForm(Interface):
    """A form to edit synchronization settings."""


class ISyncSettings(model.Schema):
    """Global settings."""

    sync_immediately = schema.Bool(
        description=_(
            u"If activated, a synchronization will be tried right away. If it fails, "
            u"the content item will be added to the queue.", ),
        default=False,
        required=False,
        title=_(u"Sync immediately"),
    )

    omitted_update_fields = schema.List(
        default=DEFAULT_OMITTED_UPDATE_FIELDS,
        description=_(
            u"This list contains field names which should be ignored when the remote "
            u"item already exists. Add one item per line."),
        required=False,
        title=_(u"Ignored fields for update"),
        value_type=schema.TextLine(),
    )

    #    directives.widget("targets", MultiWidget)
    #    directives.widget(targets=DataGridFieldFactory)
    targets = schema.List(
        description=_(u"Synchronization targets"),
        required=False,
        title=_(u"Targets"),
        value_type=schema.TextLine(title="foo")
        #        value_type=DictRow(
        #            description=_(
        #               u"Please specify targets in the form of “key|title|url|username|password”."
        #            ),
        #            title=_(u"Target definition"),
        #            schema=ITargetRow
        #        )
    )

    directives.mode(ISyncControlPanelForm, queue="display")
    queue = schema.Set(
        description=_(
            u"A list of content items which should be synced with next "
            u"synchronization run."),
        required=False,
        title=_(u"Sync Queue"),
        value_type=schema.TextLine(title=_(u"Path")),
    )


@implementer(ISyncControlPanelForm)
class SyncControlPanelForm(controlpanel.RegistryEditForm):
    """Sync control panel form."""

    schema = ISyncSettings
    schema_prefix = "collective.contentsync"
    label = _(u"Plone Sync Settings")
    buttons = controlpanel.RegistryEditForm.buttons.copy()
    handlers = controlpanel.RegistryEditForm.handlers.copy()

    def updateActions(self):  # noqa: N802
        super(SyncControlPanelForm, self).updateActions()
        if "run_sync" in self.actions:
            self.actions["run_sync"].addClass("destructive")

    @button.buttonAndHandler(
        _(u"Sync queued items now"),
        name="run_sync",
    )
    def handle_run_sync(self, action):
        sync_queue()
        plone.api.portal.show_message(
            message=_(u"Synchronization run was successful."),
            request=self.request,
        )
        self.request.response.redirect(u"{0}/{1}".format(
            plone.api.portal.get().absolute_url(),
            "@@collective.contentsync-settings"))

    @button.buttonAndHandler(
        _(u"Full sync"),
        name="full_sync",
    )
    def handle_full_sync(self, action):
        queue = plone.api.portal.get_registry_record(
            "collective.contentsync.queue")
        queue = queue or set()
        missed = full_sync()
        queue = queue & missed
        plone.api.portal.set_registry_record("collective.contentsync.queue",
                                             queue)


SyncControlPanelView = layout.wrap_form(SyncControlPanelForm,
                                        ControlPanelFormWrapper)
