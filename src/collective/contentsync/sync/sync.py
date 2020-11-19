# -*- coding: utf-8 -*-
"""Synchronization."""

from base64 import standard_b64encode
from collective.contentsync.logger import LOG
from collective.contentsync.sync.behaviors import ISyncSettings
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import copy
import plone.api
import requests


BASE_OMITTED_KEYS = [
    "@components",
    "@id",
    "allow_discussion",
    "changeNote",
    "is_folderish",
    "next_item",
    "parent",
    "previous_item",
    "review_state",
    "sync_disabled",
    "sync_settings",
    "version",
    "versioning_enabled",
]


def _extract_data(context):
    serializer = getMultiAdapter((context, context.REQUEST), ISerializeToJson)
    if not serializer:
        return

    content = serializer(include_items=False)
    # Insert default_page information
    if "default_page" not in content:
        default_page = context.getDefaultPage()
        if default_page is not None:
            content["default_page"] = default_page
    return content


def _handle_vocabulary(value):
    return value["token"]


def _handle_file_field(value, key=None, context=None):
    base64_filedata = ""
    field = getattr(context, key)
    if field and field.data:
        base64_filedata = standard_b64encode(field.data)
    return {
        "data": base64_filedata,
        "encoding": "base64",
        "filename": value.get("filename"),
        "content-type": value.get("content-type", "text/plain"),
    }


def _handle_dict(value, key=None, context=None):
    dict_keys = value.keys()
    if "token" in dict_keys:
        # Handle vocabulary
        return _handle_vocabulary(value)
    elif "scales" in dict_keys:
        # Handle image field
        return _handle_file_field(value, key=key, context=context)
    elif "filename" in dict_keys:
        # Handle file field
        return _handle_file_field(value, key=key, context=context)
    return value


def _handle_list(value, key=None, context=None):
    new_value = []
    for list_item in value:
        if isinstance(list_item, dict):
            new_value.append(_handle_dict(list_item, key=key, context=context))
        else:
            new_value.append(list_item)
    return new_value


def _prepare_data(data, context=None, full=True):
    """Remove omitted keys from data."""
    omitted_keys = []
    omitted_keys.extend(BASE_OMITTED_KEYS)
    if not full:
        omitted_keys.extend(
            plone.api.portal.get_registry_record(
                name="collective.contentsync.omitted_update_fields", default=[]
            )
        )
    for key, value in copy.deepcopy(data).items():
        if key in omitted_keys:
            del data[key]
            continue
        if isinstance(value, dict):
            data[key] = _handle_dict(value, key=key, context=context)
        elif isinstance(value, list):
            data[key] = _handle_list(value, key=key, context=context)
    return data
    # return json.dumps(data, sort_keys=True, separators=(", ", ": "))


def get_closest_enabled_sync_settings(context):
    """Return the closest enabled sync settings or None."""
    try:
        context_adapter = ISyncSettings(context)
    except TypeError:
        pass
    else:
        if not context_adapter.sync_settings and context_adapter.sync_disabled:
            return
        for setting in context_adapter.sync_settings:
            if (
                setting.get("sync_enabled", False)
                and setting.get("sync_target", None)  # noqa: W503
                and setting.get("sync_target_path", None)  # noqa: W503
            ):
                return context_adapter

    for item in context.aq_chain:
        try:
            parent_adapter = ISyncSettings(item)
        except TypeError:
            continue
        else:
            for setting in parent_adapter.sync_settings:
                if (
                    setting.get("sync_enabled", False)  # noqa: W503
                    and setting.get("sync_target", None)  # noqa: W503
                    and setting.get("sync_target_path", None)  # noqa: W503
                    and setting.get("sync_include_subcontent", False)  # noqa: W503
                ):
                    return parent_adapter
            # Check if a parent of current context has sync disabled.
            # Then we stop.
            if parent_adapter.sync_disabled:
                return
    return


def get_auth_information():
    """Login to all available targets and get the auth token for further requests."""
    items = {}
    targets = plone.api.portal.get_registry_record(name="collective.contentsync.targets")
    for target in targets:
        try:
            target_id, _, target_url, username, password = target.split("|")
        except ValueError:
            continue
        response = requests.post(
            "{0}/@login".format(target_url),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "login": username,
                "password": password,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(f'Login to {target_url} with account {username} failed (HTTP {response.status_code}). Ensure that plone.restapi is enabled on the target Plone site')
        data = response.json()
        token = data.get("token", None)
        if token:
            items[target_id] = {
                "token": token,
                "url": target_url,
            }
    return items


def _create_new_remote_content(url, token, new_content, context_uid, context=None):
    """Try to create a new content item on the target site."""
    if url.endswith("/"):
        parent_url = "/".join(url.rsplit("/")[:-2])
    else:
        parent_url = "/".join(url.rsplit("/")[:-1])

    create_response = requests.post(
        parent_url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        json=_prepare_data(new_content, context=context),
    )
    if create_response.status_code != 201:
        LOG.warn("Remote content could not be created at {0}!".format(url))
        return False

    # Try to patch the UID
    if url.endswith("/"):
        patch_uid_url = "{0}@updateuid".format(url)
    else:
        patch_uid_url = "{0}/@updateuid".format(url)

    patch_uid_response = requests.patch(
        patch_uid_url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        json={"UID": context_uid},
    )
    if patch_uid_response.status_code != 204:
        LOG.warn("UID patch was not successful for {0}!".format(patch_uid_url))
    return True


def _set_remote_default_page(url, token, new_content):
    # Try to patch the default_page
    if url.endswith("/"):
        patch_default_page_url = "{0}@setdefaultpage".format(url)
    else:
        patch_default_page_url = "{0}/@setdefaultpage".format(url)

    patch_default_page_response = requests.patch(
        patch_default_page_url,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        json={"default_page": new_content["default_page"]},
    )
    if patch_default_page_response.status_code != 204:
        LOG.warn(
            "Setting default page was not successful for {0}!".format(
                patch_default_page_url
            )
        )


def run_sync(context, settings=None, auth=None):
    """Sync a content item based on the sync configuration."""
    if not settings:
        settings = get_closest_enabled_sync_settings(context)

    if not settings:
        return False

    status = True

    context_path = "/".join(context.getPhysicalPath())
    LOG.info("Running sync for {0}".format(context_path))

    if not auth:
        auth = get_auth_information()

    # 1. get JSON content from context
    new_content = _extract_data(context)

    for setting in settings.sync_settings:
        if not setting.get("sync_enabled", False):
            continue
        target_id = setting.get("sync_target", None)
        target = auth.get(target_id)
        path = setting.get("sync_target_path", None)
        if not target or not path:
            continue

        base_url = target.get("url", None)
        if not base_url:
            continue

        if not base_url.endswith("/") and not path.startswith("/"):
            url = "/".join([base_url, path])
        else:
            url = "".join([base_url, path])

        if settings.context != context:
            # We sync a sub content item
            relative_path = context_path.split(
                "/".join(settings.context.getPhysicalPath())
            )[-1]
            url = "".join([url, relative_path])

        token = target.get("token", None)
        context_uid = plone.api.content.get_uuid(context)

        # 2. Check if content already exisits
        check_response = requests.get(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer {0}".format(token),
            },
        )
        if check_response.status_code == 404:
            # 3. if no, try create content in parent
            status = _create_new_remote_content(
                url, token, new_content, context_uid, context=context
            )

        elif check_response.status_code == 200:
            # 4. if yes, check if UID matches
            data = check_response.json()
            remote_uid = data.get("UID", None)
            if remote_uid != context_uid:
                LOG.warn(
                    "Remote UID does not match content UID at {0}!".format(url)
                )
                status = False
                continue

            # 5. if yes, update (PATCH) content
            patch_response = requests.patch(
                url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {0}".format(token),
                },
                json=_prepare_data(new_content, context=context, full=False),
            )
            if patch_response.status_code != 204:
                LOG.warn("Content update was not successful for {0}!".format(url))
                status = False
                continue

        if "default_page" in new_content:
            _set_remote_default_page(url, token, new_content)

    LOG.info("Finished sync for {0}".format(context_path))
    return status


def sync_queue():
    """Sync all items from the queue."""
    queue = plone.api.portal.get_registry_record("collective.contentsync.queue")
    queue = queue or set()
    if not queue:
        return

    auth_token = get_auth_information()
    for item in list(queue):
        obj = plone.api.content.get(path=item)
        sync_result = run_sync(obj, auth=auth_token)
        if sync_result is True:
            # Remove item from the list
            queue.remove(item)
    plone.api.portal.set_registry_record("collective.contentsync.queue", queue)


def _sync_enabled(settings):
    for setting in settings:
        if (
            setting.get("sync_enabled", False)
            and setting.get("sync_target", None)  # noqa: W503
            and setting.get("sync_target_path", None)  # noqa: W503
        ):
            return True
    return False


def _subcontent_sync_enabled(settings):
    for setting in settings:
        if (
            setting.get("sync_enabled", False)
            and setting.get("sync_target", None)  # noqa: W503
            and setting.get("sync_target_path", None)  # noqa: W503
            and setting.get("sync_include_subcontent", False)  # noqa: W503
        ):
            return True
    return False


def _get_subcontent_items(context):
    result = set()
    for brain in plone.api.content.find(context=context):
        if not brain.has_sync_disabled:
            result.add(brain.getPath())
    return result


def full_sync(sync_path=None):
    """Get all content items with sync option and run sync."""


    # 1. get all sync_enabled content
    sync_queue = set()

    query = dict(has_sync_enabled=True)
    if sync_path:
        if sync_path.startswith("/"):
            sync_path = sync_path.lstrip("/")
        sync_obj = plone.api.content.portal.get().restrictedTraverse(sync_path, None)
        if sync_obj is None:
            raise ValueError(f"No sync-enabled object found at {sync_path}")
        query["path"] = '/'.join(sync_obj.getPhysicalPath())
        LOG.warn(f"Limiting sync to content object at {sync_path}")

    for sync_brain in plone.api.content.find(**query):
        context = sync_brain.getObject()
        try:
            adapter = ISyncSettings(context)
        except TypeError:
            continue
        else:
            if _sync_enabled(adapter.sync_settings):
                sync_queue.add("/".join(context.getPhysicalPath()))
            if _subcontent_sync_enabled(adapter.sync_settings):
                # 2. get all subcontent for each sync enabled content
                sync_queue.update(_get_subcontent_items(context))

    # 3. get auth token
    auth_token = get_auth_information()

    # 4. iterate over queue, sort by path, and run sync on all items
    items = sorted(list(sync_queue))
    num_items = len(items)
    for i, item in enumerate(items):
        # LOG.info() but be correct (but does not log anything through
        # scripts/run-sync.py
        LOG.warn(f"Processing {i+1}/{num_items}: {item}")
        obj = plone.api.content.get(path=item)
        try:
            sync_result = run_sync(obj, auth=auth_token)
        except Exception as e:
            LOG.warn(f"Unable to sync {item}: {e}", exc_info=True)
            continue
        if sync_result is True:
            # Remove item from the list
            sync_queue.remove(item)
    return sync_queue
