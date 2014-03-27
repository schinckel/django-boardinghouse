Included Extensions
===================

.. _invite::

boardinghouse.contrib.invite
----------------------------

One of the real ideas for how this type of system might work is `Xero`_, which allows a user to invite other people to access their application. This is a little more than just the normal registration process, as if the user is an existing Xero user, they will get the opportunity to link this Xero Organisation to their existing account.

Then, when they use Xero, they get the option to switch between organisations... sound familiar?

The purpose of this contrib application is to provide forms, views and url routes that could be used, or extended, to recreate this type of interaction.

The general pattern of interaction is:

* User with required permission (invite.create_invitation) is able to generate an invitation. This results in an email being sent to the included email address (and, if a matching email in this system, an entry in the pending_acceptance_invitations view), with the provided message.

.. note:: Permission-User relations should really be per-schema, as it is very likely that the same user will not have the same permission set within different schemata. This can be enabled by using :ref:`roles`, for instance.

* Recipient is provided with a single-use redemption code, which is part of a link in the email, or embedded in the view detailed above. When they visit this URL, they get the option to accept or decline the invitation.

* Declining the invitation marks it as declined, provides a timestamp, and prevents this invitation from being used again. It is still possible to re-invite a user who has declined (but should provide a warning to the logged in user that this user has already declined an invitation).

* Accepting the invitation prompts the user to either add this schema to their current user (if logged in), or create a new account. If they are not logged in, they get the option to create a new account, or to log in and add the schema to that account. Acceptance of an invitation prevents it from being re-used.

It is possible for a logged in user to see the following things (dependent upon permissions in the current schema):

* A list of pending (non-accepted) invitations they (and possibly others) have sent.

* A list of declined and accepted invitations they have sent.

* A list of pending invitation they have not yet accepted or declined. This page can be used to accept or decline.

.. _Xero: http://www.xero.com

.. _roles:

boardinghouse.contrib.roles
---------------------------

.. note:: This app has not been developed.

This app enables per-schema roles, which are a basically the same as the normal django groups, except they are not a SharedSchemaModel.

They are intended for end-user access and configuration.


.. _shared_roles:

boardinghouse.contrib.shared_roles
----------------------------------

.. note:: This app has not been developed.

This app alters the `django.contrib.auth` application, so that, whilst the `Group` model remains a `SharedSchemaModel`, the relationships between `User` and `Group`, and the relationship between `User` and `Permission` are actually schema-aware.


.. _demo:

boardinghouse.contrib.demo
--------------------------

.. note:: This app has not been developed.

Borrowing again from `Xero`_, we have the ability to create a demo schema: there can be at most one per user, and it expires after a certain period of time, can be reset at any time by the user, and can have several template demos to be based upon.


.. _audit:

boardinghouse.contrib.audit
---------------------------

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
