# -*- coding: utf8 -*-

from Products.Five.browser import BrowserView

import plone.api


class SyncAssignments(BrowserView):
    def get_assignments(self):
        """ Find objects with sync settings """
        catalog = plone.api.portal.get_tool("portal_catalog")
        result = dict(sync_enabled=[], sync_disabled=[])
        brains = catalog(has_sync_enabled=True)
        for brain in brains:
            obj = brain.getObject()
            if obj.sync_settings:
                result["sync_enabled"].append(
                    dict(path=brain.getPath(),
                         href=brain.getURL(),
                         title=brain.Title,
                         sync_settings=obj.sync_settings))
        brains = catalog(has_sync_disabled=True)
        for brain in brains:
            obj = brain.getObject()
            if obj.sync_settings:
                result["sync_enabled"].append(
                    dict(path=brain.getPath(),
                         href=brain.getURL(),
                         title=brain.Title,
                         sync_settings=obj.sync_settings))
        return result
