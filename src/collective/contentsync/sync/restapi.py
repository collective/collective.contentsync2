# -*- coding: utf-8 -*-
"""plone.restapi extensions."""

from plone.restapi.deserializer import json_body
from plone.restapi.services import Service
from zExceptions import BadRequest, Unauthorized
from zope.interface import alsoProvides

import plone.protect.interfaces


class UpdateUID(Service):
    """Update the UID for the given content object."""
    def reply(self):
        data = json_body(self.request)
        uuid = data.get("UID", None)

        if not uuid:
            raise BadRequest("Property 'UID' is required")

        # Disable CSRF protection
        if "IDisableCSRFProtection" in dir(plone.protect.interfaces):
            alsoProvides(self.request,
                         plone.protect.interfaces.IDisableCSRFProtection)

        try:
            setattr(self.context, "_plone.uuid", uuid)
            self.context.reindexObject(idxs=["UID"])
        except Unauthorized as exc:
            self.request.response.setStatus(403)
            return dict(error=dict(type="Forbidden", message=str(exc)))
        except BadRequest as exc:
            self.request.response.setStatus(400)
            return dict(error=dict(type="Bad Request", message=str(exc)))

        return self.reply_no_content()


class SetDefaultPage(Service):
    """Set the default page for the given content object."""
    def reply(self):
        data = json_body(self.request)
        default_page = data.get("default_page", None)
        try:
            self.context.setDefaultPage(default_page)
        except Unauthorized as exc:
            self.request.response.setStatus(403)
            return dict(error=dict(type="Forbidden", message=str(exc)))
        except BadRequest as exc:
            self.request.response.setStatus(400)
            return dict(error=dict(type="Bad Request", message=str(exc)))

        return self.reply_no_content()
