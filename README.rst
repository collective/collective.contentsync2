.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.


=======================
collective.contentsync2
=======================

Content sync between Plone sites over plone.restapi

Documentation
-------------

- Full documentation: https://collectivecontentsync2.readthedocs.io/en/latest/

Features
--------

- sync content folders or individual content objects to a remote Plone site
- full sync for initial sync 
- incremental sync for content updates
- configurable sync behavior per content type
- trigger immediate sync upon create or update operations through content rules

Description
-----------

This add-on can be used to push changes from one Plone site to a list of
configured other Plone sites (one-way-sync). They should have the same Plone
Major versions, but it is not required. Depending on the content which is
synced, the installed add-ons should match. The add-on uses plone.restapi to
push the content.

You can configure a list of target sites (the Plone sites you want to sync to),
with URL, username and password for a user who has at least the Contributor
role.

To enable the content sync (push), you need to add a content rule with the
content sync action. There is nothing more to configure for that rule, but it
needs to be enabled either for the whole site or just a sub tree. So it is up
to you when the sync should happen (content added, workflow changed, ...).

The add-on comes with a behavior (an action and a manage screen would work too,
but for the customer the behavor was the easier way). There you can add a
configuration for all configured targets. The content sync can be enabled and
also include all sub items. It also contains an option to exclude an item from
the sync process.

With that you have almost unlimited options. For example, a products folder can
be synced from example.com to sub1.example.com/products and
sub2.example.com/products. Now one item in that products folder should not be
synced to sub1, but to sub2. This can be achieved by excluding the item from
sync, and then by adding a new sync configuration for sub2 starting at this
point.

The add-on allows you to sync content immediately, manually or triggered by a
cron job. This can be adjusted in the control panel. To sync via cron job, best
is to create an instance script which calls the full sync method and call that
with your cron job.

By default, only the object that triggered the content rule will be synced, not
the sub content. This is to prevent long running tasks. You can do a full sync
to sync all content, or just the items left in the queue (which might have
failed for some reason).

There is also an option to exlude fields for updates. So when an item is
created, all fields are synced. But on update you can choose which are ignored
(e.g. for local customizations on the target site).

One more thing: the sync will only update existing content on the target site
if the UID matches. For this to work there is a new restapi service to update
the UID after the item was created on the target site. Maybe this (passing the
UID) can be included in the restapi service for creating content.



Software requirements
---------------------

- Plone 5.2 or higher
- Python 3
- no support for Plone sites running on Python 2

Installation
------------

`collective.contentsync2` must be installed both on the source **and** target
Plone site through buildout::

    [buildout]

    ...

    eggs =
        collective.contentsync2


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.contentsync2/issues
- Source Code: https://github.com/collective/collective.contentsync2

License
-------

The project is licensed under the GPLv2.

Authors
-------

- Thomas Massmann (primary author)
- Andreas Jung (collective.contentsync2 refactoring)


