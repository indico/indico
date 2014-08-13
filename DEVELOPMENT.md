Tips for developers
-------------------
It's dangerous to go alone. Take these tips in case you need to fit Indico to your particular needs.

## SQLAlchemy
For the moment, we are focusing on _PostgreSQL_. These are some of the specific calls that you'd need to change in case
you want to use a different relational database such as MySQL (don't do it, you will spend much more time on it than
installing PostgreSQL would take!):

* `array_agg()`, since MySQL doesn't have ARRAY type. You can find occurrences of them within:
    - _indico/modules/rb/models/locations.py_
    - _indico/modules/rb/models/rooms.py_

* ReservationEditLog uses a PostgreSQL ARRAY to store the changes for a single log entry

* calculate_rooms_booked_time uses `extract('dow')` PostgreSQL specific for day of the week.

In some cases you have properties in your models which trigger additional queries or are expensive for some other reason.
Sometimes you can simply write tricky queries to retrieve all data at once, but in other cases that's not feasible,
either because of what the property does or because you need it for serializing and thus only have the object itself
available.  But caching is easy: Simply use the `@cached` decorator from `indico.modules.rb.models.utils` combined with
the `versioned_cache` mixin. For details, see the docstrings of these functions.


## Initializing the database
Use `indico db prepare` to create your tables based on the SQLAlchemy models and set the migration status to the most
recent alembic revision.

If you want to import data from ZODB, run `bin/migration/migrate_to_sqlalchemy.py` with the appropriate arguments.


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
value set to whatever default value you want. Afterwars, use the `alter_column` operation to remove the default value.
While keeping it would not hurt, it's better to stay in sync with the SQLAlchemy model!
