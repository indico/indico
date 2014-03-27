Tips for developers
-------------------
It's dangerous to go alone. Take these tips in case you need to fit Indico to your particular needs.

## SQLAlchemy
For the moment, we are focusing on _PostgreSQL_. These are some of the specific calls that you'd need to change in case you want to use a different relational database such as MySQL:

* `array_agg()`, since MySQL doesn't have ARRAY type. You can find occurrences of them within:
    - _indico/modules/rb/models/locations.py_
    - _indico/modules/rb/models/rooms.py_
