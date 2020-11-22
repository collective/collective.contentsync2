.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.


======================
collective.contentsync
======================

Content sync between Plone sites over plone.restapi

Features
--------

- sync content folders or individual content objects to a remote Plone site
- full sync for initial sync 
- incremental sync for content updates
- configurable sync behavior per content type
- trigger immediate sync upon create or update operations through content rules

Software requirements
---------------------

- Plone 5.2 or higher
- Python 3
- no support for Plone sites running on Python 2

Installation
------------

`collective.contentsync` must be installed both on the source **and** target
Plone site through buildout::

    [buildout]

    ...

    eggs =
        collective.contentsync


Configure the target Plone site(s) using the `Sync settings` inside the Plone control panel.

Preparations on your target Plone site
######################################

- install/enable `plone.restapi` and `collective.contentsync` through the Plone
  add-ons control panel
- create a dedicated user account e.g. `content_sync` with `Site Adminstrator` or `Editor` role
- use this user account and its password inside the `targets` configuration of
  the source system (see below)

Preparations on your source Plone site
######################################

- install/enable `plone.restapi` and `collective.contentsync` through the Plone
  add-ons control panel
- enable the `Content sync` behavior on the content types that you want to sync.
  Usually you want to sync a folder and its subcontent. So you would enable the
  behavior on the `Folder` content-type within the content-types controlpanel
  of Plone.

Configure a content object for syncing
######################################


Run `Full sync` on the source Plone site for an initial full sync.

Incremental sync: to be documented

Content rules: to be documented


Contribute
----------

- Issue Tracker: https://github.com/collective/collective.contentsync/issues
- Source Code: https://github.com/collective/collective.contentsync

License
-------

The project is licensed under the GPLv2.

Authors
-------

- Thomas Massmann (primary author)
- Andreas Jung (collective.contentsync refactoring)

