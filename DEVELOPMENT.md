Tips for developers
-------------------
It's dangerous to go alone. Take these tips in case you need to fit Indico to your particular needs.

## Initializing the database
Use `indico db prepare` to create your tables based on the SQLAlchemy models and set the migration status to the most
recent alembic revision.


## SQL Database migrations
Whenever you modify the database structure or want to perform data migrations, create an alembic revision.
To do so, use `indico db revision -m 'short explanation'`; optionally you may specify `--autogenerate` to let Alembic
compare your SQLAlchemy models with your database and generate migrations automatically. However, this is not 100%
reliable and for example functional indexes will always show up as "new". So if you use autogeneration, **always**
check the generated migration steps and modify them if necessary. Especially if you've already applied your change to the
database manually or let SQLAlchemy create your new table you need to write the migration for it manually or DROP the
table again so Alembic knows it's new.

To perform the actual migration of the database, run `indico db upgrade` or `indico db downgrade`. Migration should
always be possible in both directions, so when writing a migration step make sure to test it and to implement both
directions for structure and data even if that means dropping columns or tables. Losing data during a downgrade is
acceptable as long as it's data that didn't exist before that revision. Please make sure to TEST migration in both
directions!

When adding a new column that is not nullable, you need to add it in two steps: First create it with a `server_default`
value set to whatever default value you want. Afterwards, use the `alter_column` operation to remove the default value.
While keeping it would not hurt, it's better to stay in sync with the SQLAlchemy model!


## Writing models
When writing/changing models or alembic revisions, run `python bin/maintenance/update_backrefs.py` to keep comments
about relationship backrefs in sync and `python bin/utils/db_diff.py` to compare the models against your current
database both to ensure your alembic revision is correct and that your own database is up to date.
