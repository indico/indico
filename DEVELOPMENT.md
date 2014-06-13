Tips for developers
-------------------
It's dangerous to go alone. Take these tips in case you need to fit Indico to your particular needs.

## SQLAlchemy
For the moment, we are focusing on _PostgreSQL_. These are some of the specific calls that you'd need to change in case you want to use a different relational database such as MySQL:

* `array_agg()`, since MySQL doesn't have ARRAY type. You can find occurrences of them within:
    - _indico/modules/rb/models/locations.py_
    - _indico/modules/rb/models/rooms.py_

* ReservationEditLog uses a PostgreSQL ARRAY to store the changes for a single log entry

In some cases you have properties in your models which trigger additional queries or are expensive for some other reason.
Sometimes you can simply write tricky queries to retrieve all data at once, but in other cases that's not feasible,
either because of what the property does or because you need it for serializing and thus only have the object itself
available.  But caching is easy: Simply use the `@cached` decorator from `indico.modules.rb.models.utils` combined with
the `versioned_cache` mixin. For details, see the docstrings of these functions.
