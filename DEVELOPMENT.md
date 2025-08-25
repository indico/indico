Tips for developers
-------------------
It's dangerous to go alone. Take these tips in case you need to fit Indico to your particular needs.

## Hiding noisy reformat commits from `git blame`
Run `git config --global blame.ignoreRevsFile .git-blame-ignore-revs` to make git ignore those commits.
When you run a code formatter on the codebase, make sure to add the new commit there as well. Note that it
has to be the full commit hash, using a shorthash will break `git blame`.

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


## Updating Python dependencies
We use [uv](https://github.com/astral-sh/uv) to manage our `requirements.txt` files. To update the pinned
dependencies, use `./bin/maintenance/compile-python-deps.py -U`; if you just want to update a specific dependency
that's also possible (`-P packagename`). Afterwards, check the diff for the requirements.txt files and consult
each package's changelog for important changes in case of direct dependencies that aren't just patch releases.
Once that's done, you MUST install Indico with `pip install -e '.[dev]'` and ensure nothing is broken (depending on
what changed, make sure to test affected parts manually).

Adding new Python dependencies is done in a similar way: Add them to the correct `requirements.in` file, and then run
`./bin/maintenance/compile-python-deps.py` to generate the `requirements.txt` files. DO NOT upgrade deps while adding
a new one, if whatever you add depends on a newer version of an existing dependency try to update only that one, or
open a separate PR to do the dependency updates first.


## JS dependencies
To update deps within semver ranges, `rm -rf package-lock.json node_modules` followed by `npm install` usually does
the job. Make sure to restart the `build-assets.py` script afterwards to ensure things like the webpack build aren't
broken. It's also recommended to test both dev and prod builds, and to build plugins. For plugins, it's recommended
to try both the normal and CERN plugins (since some of those such as the Burotel plugin use more 'magic' than the
standard ones).

Once that's done, `npm outdated -l` will list the remaining packages to be updated. Often the semver-major changes
are simply dropping support for old node versions and similar harmless things. But certain other packages are known
to be problematic. Here's a list to save some time during the next updates:

- `@dr.pogodin/babel-plugin-react-css-modules`, `css-loader` and `mini-css-extract-plugin` are very prone to problems
  if not all of them have the versions the other packages expect. Trying to update `css-loader` to the latest major
  version is not straightforward either. It's best to leave those packages alone until we either drop webpack or
  look into webpack's [asset modules](https://webpack.js.org/guides/asset-modules/) feature.
- `dropzone` is still on a stable release, the new version is still in beta so not worth considering.
- `history`, `react-router` and `react-router-dom` have some major changes e.g. regarding navigation blocking. It
  looks like they finally added `unstable_useBlocker()` to block navigation though. In the Room Booking module we
  are using `connected-react-router` though, which is dead, and not compatible with react-router 6 so it would need
  to be replaced with something else first.
- `husky` could in principle be updated, but we use it in a very basic way (to setup and run the pre-commit git hook),
  and there is no need to switch to the newer and slightly more complex configuration of newer versions.
- `jquery-ui` stays on `^1.12.1` until we can get rid of it one day. Newer versions break focusing input elements inside
  react dialogs opened from a jquery ui modal.
- `react-dnd` and `react-dnd-html5-backend`: TODO
- `react` and `react-dom` would be great candidates to update, but it's stuck until react-dates starts supporting React 18
  (react-dates/react-dates#2199) which depends on Enzyme supporting it (enzymejs/enzyme#2524)
- `react-dropzone` requires MIME types instead of just file extensions for the files it should accept in newer versions,
  but we have various places where we have only file extensions, so we can't easily update.
- `react-leaflet`, `react-leaflet-draw` and `react-leaflet-markercluster` are stuck because react-leaflet v3 decided to
  adept some dumb "ethical" license (PaulLeCam/react-leaflet#698) which is not considered a proper Open Source license.
- `react-markdown`, `react-redux`, `redux`, `redux-thunk` and `reselect` are stuck because react-redux now requires react 18, but react-dates does not support this.
- `stylelint`, `stylelint-config-recommended-scss` and `stylelint-scss` had a common major version bump, possibly breaking compatibility with `stylelint-prettier` (which we no longer use). Should be tested to confirm whether that's indeed the case, but for now it's easier to simply stick with the old version.
