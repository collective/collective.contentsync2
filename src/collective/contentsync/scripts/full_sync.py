# -*- coding: utf8 -*-
# Usage:  bin/instance run scripts/full_sync.py <plone-site-id> <optional: /path/sync/object>

import os
import sys
import argparse 

import transaction
from zope.component.hooks import setSite
from AccessControl.SecurityManagement import newSecurityManager

from collective.contentsync.sync.sync import full_sync


def main(app, args):

    admin_user = os.environ.get('ADMIN_USER', 'admin')
    acl_users = app.acl_users
    user = acl_users.getUser(admin_user)
    if user is None:
        raise ValueError(f'No user account "{admin_user}" found in /acl_users. Override account by setting the $ADMIN_USER environment variable')
    newSecurityManager(None, user.__of__(acl_users))

    if len(args) == 4:
        site_id = sys.argv[-1]
        sync_path = None
    elif len(args) == 5:
        site_id, sync_path = sys.argv[-2:]
    else:
        print("Usage:  bin/instance run scripts/full-sync.py <plone-site-id> <optional: /path/sync/object>")
        print("\n")
        print("Example:  bin/instance run scripts/full-sync.py dynamore /en/downloads")
        sys.exit(1)

    if not site_id in app.objectIds():
        raise ValueError(f'No Plone site "{site_id}" found')
    site = app[site_id]
    setSite(site)

    print("Starting full sync")
    full_sync(sync_path=sync_path)
    transaction.commit()
    print("Finished with full sync")

if 'app' in locals():
    main(app, sys.argv)
