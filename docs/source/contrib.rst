Included Extensions
===================

.. _invite:

boardinghouse.contrib.invite
----------------------------

.. note:: This app is incomplete.

One of the real ideas for how this type of system might work is `Xero`_, which allows a user to invite other people to access their application. This is a little more than just the normal registration process, as if the user is an existing Xero user, they will get the opportunity to link this Xero Organisation to their existing account.

Then, when they use Xero, they get the option to switch between organisations... sound familiar?

The purpose of this contrib application is to provide forms, views and url routes that could be used, or extended, to recreate this type of interaction.

The general pattern of interaction is:

* User with required permission (invite.create_invitation) is able to generate an invitation. This results in an email being sent to the included email address (and, if a matching email in this system, an entry in the pending_acceptance_invitations view), with the provided message.

* Recipient is provided with a single-use redemption code, which is part of a link in the email, or embedded in the view detailed above. When they visit this URL, they get the option to accept or decline the invitation.

* Declining the invitation marks it as declined, provides a timestamp, and prevents this invitation from being used again. It is still possible to re-invite a user who has declined (but should provide a warning to the logged in user that this user has already declined an invitation).

* Accepting the invitation prompts the user to either add this schema to their current user (if logged in), or create a new account. If they are not logged in, they get the option to create a new account, or to log in and add the schema to that account. Acceptance of an invitation prevents it from being re-used.

It is possible for a logged in user to see the following things (dependent upon permissions in the current schema):

* A list of pending (non-accepted) invitations they (and possibly others) have sent.

* A list of declined and accepted invitations they have sent.

* A list of pending invitation they have not yet accepted or declined. This page can be used to accept or decline.

.. _Xero: http://www.xero.com

.. _template:

boardinghouse.contrib.template
------------------------------

Introduces the concept of :class:`SchemaTemplate` objects, which can be used to create a schema that contains initial data.

.. note::  A template can only be activated by a superuser or staff member (`User.is_superuser` or `User.is_staff`). We can't use permissions here, because they are stored per-schema, so it would depend on which schema is active.

Settings
~~~~~~~~

* `BOARDINGHOUSE_TEMPLATE_PREFIX` (default `__tmpl_`)

When installed, this app monkey-patches the installed `ModelAdmin` for the schema model, and adds a field to the create form, allowing for selecting a template to clone from. It also adds an admin action that clones an existing schema object (or objects) into a template: a process which clones the source schemata, including their content.


.. _groups:

boardinghouse.contrib.groups
----------------------------

By default, django-boardinghouse puts all of the `django.contrib.auth` models into the "shared" category, but maintains the relationships between `User` ⟷ `Permission`, and between `User` ⟷ `Group` as private/per-schema relationships. This actually makes lots of sense, as authorisation to perform an action belongs to the schema.

The relationship between `Group` ⟷ `Permission` is also shared: the philosophy here is that everything except group *allocation* (and per-user permission) should be maintained by the system administrator, not by schema owners.

However, if you desire the `Group` instances to be per-schema (and by inference, the `Group` ⟷ `Permission` relations), then installing this package makes this possible.


.. _demo:

boardinghouse.contrib.demo
--------------------------

Building on the `boardinghouse.contrib.template` app, the `demo` app allows for each user to have at most one current demo. This is a fully operational schema, cloned from a template, but has an expiry date. A demo may be reset by the user, which clears out all of the changes different from the template and resets the expiry period.

Settings:

* `BOARDINGHOUSE_DEMO_PERIOD`
* `BOARDINGHOUSE_DEMO_PREFIX`

Expired demos may not be activated.

There should be a way to turn an expired demo into a full schema.

There is a supplied management command `cleanup_expired_demos`, which removes all expired demos. (This should only remove those that expired more than X ago, which should be a setting).

There are supplied views for handling the different actions on Demo objects:

.. automodule:: boardinghouse.contrib.demo.views


.. _access:

boardinghouse.contrib.access
----------------------------

.. note:: This app is still being planned.

Store the last accessor of each schema, like in the `Xero`_ dashboard view.

Organisations

+-----------------------+---------------------+------------------+
| Name                  | Last accessed       | Role             |
+-----------------------+---------------------+------------------+
| Larson, Inc.          | Today, 5:58pm       | Adviser          |
|                       | by Bob Smith        |                  |
+-----------------------+---------------------+------------------+
| Leffler, Mertz and    | Today, 7:58pm       | Adviser          |
| Roberts               | by Bob Smith        |                  |
+-----------------------+---------------------+------------------+
