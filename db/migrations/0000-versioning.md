# NAME

**Versioning** - simplistic take on tracking and applying changes to databases.

# DESCRIPTION

This project strives to provide simple way to manage changes to
database.

Instead of making changes on development server, then finding
differences between production and development, deciding which ones
should be installed on production, and finding a way to install them -
you start with writing diffs themselves!

# INSTALLATION

To install versioning simply run install.versioning.sql in your database
(all of them: production, stage, test, devel, ...).

# USAGE

In your files with patches to database, put whole logic in single
transaction, and use \_v.\* functions - usually \_v.register_patch() at
least to make sure everything is OK.

For example. Let's assume you have patch files:

## 000-base.sql:

```
create table users (id serial primary key, username text);
```

## 001-users.sql:

```
insert into users (username) values ('depesz');
```

To change it to use versioning you would change the files, to this
state:

## 000-base.sql:

```
BEGIN;
select _v.register_patch('000-base', NULL, NULL);
create table users (id serial primary key, username text);
COMMIT;
```

## 001-users.sql:

```
BEGIN;
select _v.register_patch('001-users', ARRAY['000-base'], NULL);
insert into users (username) values ('depesz');
COMMIT;
```

This will make sure that patch 001-users can only be applied after
000-base.

# AVAILABLE FUNCTIONS

## \_v.register_patch( TEXT, TEXT[], TEXT[] )

Registers named patch (first argument), checking if all required patches (2nd
argument) are installed, and that no conflicting patches (3rd argument) are
installed.

2nd and 3rd arguments default to NULL/empty array.

## \_v.try_register_patch( TEXT, TEXT[], TEXT[] )

Works just like \_v.register_patch(), but instead of raising exception it
returns true if it worked, and false if it didn't.

## \_v.unregister_patch( TEXT )

Removes information about given patch from the versioning data.

It doesn't remove objects that were created by this patch - just removes
metainformation.

## \_v.assert_user_is_superuser()

Make sure that current patch is being loaded by superuser.

If it's not - it will raise exception, and break transaction.

## \_v.assert_user_is_not_superuser()

Make sure that current patch is not being loaded by superuser.

If it is - it will raise exception, and break transaction.

## \_v.assert_user_is_one_of(TEXT, TEXT, ... )

Make sure that current patch is being loaded by one of listed users.

If ```current_user``` is not listed as one of arguments - function will raise
exception and break the transaction.

# SUPPORT

If you'd like to suggest new functionality or ask anything - please use
contact information from https://depesz.com/
