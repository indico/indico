Adding models to your plugin
============================

Plugins must describe its database model the in the *models* folder if needed::

    class Foo(db.Model):
        __tablename__ = 'foo'
        __table_args__ = {'schema': 'plugin_example'}

        id = db.Column(
            db.Integer,
            primary_key=True
        )
        bar = db.Column(
            db.String,
            nullable=False,
            default=''
        )
        location_id = db.Column(
            db.Integer,
            db.ForeignKey('roombooking.locations.id'),
            nullable=False
        )
        location = db.relationship(
            'Location',
            backref=db.backref('example_foo', cascade='all, delete-orphan', lazy='dynamic'),
        )

        @return_ascii
        def __repr__(self):
            return u'<Foo({}, {}, {})>'.format(self.id, self.bar, self.location)


Thanks to **Alembic**, the migration needed to create the tables in the database can also be included in the plugin.
The steps to do so are:

1. Create a revision for the changes your plugin will add with ``indico db --plugin example migrate -m 'short description'``
2. Fine-tune the revision file generated under *migrations*.
3. Run ``indico db --plugin example upgrade`` to have Alembic upgrade your DB with the changes.
