Philosophy
==========

Multi-tenancy or multi-instance?
--------------------------------

I'll refer to multi-instance as a system where each user has an individual installation of the software, possibly on a different machine, but always running in a different database. From a web application perspective, each installation would probably have it's own domain name. It's very likely that for small applications, instances may be on the same physical machine, although they would either be in seperate Virtual Machines (at an operating system level), or in seperate VirtualHosts (in apache-speak).

Multi-tenancy, on the other hand, shares a code-base, but the data storage may be partitioned in one of several ways:

1. Foreign-key separation only.
2. Completely seperate databases.
3. Some shared data, some seperated data.

Of these, the third one is what this project deals with: although with a different perspective to other projects of a similar ilk. This is a hybrid approach to the first two, and I'll discuss here why I think this is a good way to build a system.

Firstly, though, some rationalé behind selecting a multi-tenanted over a multi-instance approach.

* Single code-base. Only one deployment is required. However, it does mean you can't gradually roll-out changes to specific tenants first (unless that is part of your code base).

* Economy of scale. It's unlikely that any given tenant will have a usage pattern that requires large amounts of resources. Pooling the tenants means you can have fewer physical machines. Again, this could be done by having virtual environments in a multi-instance approach, but there should be less overhead by having less worker threads.

* Data aggregation. It's possible (depending upon data storage) to aggregate data across customers. This can be used for comparative purposes, for instance to enable customers to see how they perform against their peers, or purely for determining patterns.

Data storage type
-----------------

It is possible to build a complex, large multi-tenanted application purely using foreign keys. That is, there is one database, and all data is stored in there. There is a single `customers` table (or equivalent), and all customer data tables contain a foreign key relationship to this table. When providing users with data to fulfill their requests, each set of data is filtered according to this relationship, in addition to the other query parameters.

This turns out to not be such a great idea, in practice. Having an extra column in every field in the database means your queries become a bit more complex. You can do away with some of the relationships (`invoices` have a relationship to `customers`, so items with a relationship to `invoices` have an implicit relationship to customers), however this becomes ever more difficult to run reports.

There are still some nice side effects to using this approach: the first and foremost is that you only need to run database migrations once. 

The other common approach is to use the same code-base, but a different database per-tenant. Each tenant has their own domain name, and requests are routed according to the domain name. There are a couple of django applications that do this, indeed some even use Postgres schemata instead of databases.

However, then you lose what can be an important feature: different tenants users access the system using different domain names.

The third approach, the one taken by this package is that there are some special tables that live in the public schema, and everything lives in a seperate schema, one per tenant.

This allows us to take advantage of several features of this hybrid structure:

* A request is routed to a specific schema to fetch data, preventing data access from all other schemata. Even programmer error related to foreign keys keeps data protected from other customers.

* It is possible to run ad-hoc queries for reporting against data within a single schema (or even multiple schemata). No need to ensure each table is filtered according to `customers`.

* Users all log in at the same domain name: users have a relationship with a schema or schemata, and if business logic permits, may select between different schemata they are associated with.

How it works
------------

Within the system, there is a special model: :class:`boardinghouse.models.Schema`. Whenever new instances of this model are created, the system creates a new Postgres schema with that name, and clones a copy of the table structure into that (from a special `__template__` schema, which never contains data).

Whenever Django changes the table structure (for instance, using ``syncdb``, or ``migrate`` from South), the DDL changes are applied to each known schema in turn.

Whenever a request comes in, :class:`boardinghouse.middleware.SchemaMiddleware` determines which schema should be active, and sets the Postgres ``search_path`` accordingly. If a user may change schema, they may request a schema activation for one of their other available schemata, and any future requests will only present data from that schema.