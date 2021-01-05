# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()


folder_created = _signals.signal('folder-created', """
Called when a new attachment folder is created.  The *sender* is the
new `AttachmentFolder` object.  The user who created the folder is
passed in the `user` kwarg.  This signal is never triggered for the
internal default folder.
""")

folder_deleted = _signals.signal('folder-deleted', """
Called when a folder is deleted.  The *sender* is the
`AttachmentFolder` that was deleted.  The user who deleted the folder
is passed in the `user` kwarg.
""")

folder_updated = _signals.signal('folder-updated', """
Called when a folder is updated.  The *sender* is the
`AttachmentFolder` that was updated.  The user who updated the folder
is passed in the `user` kwarg.
""")


attachment_created = _signals.signal('attachment-created', """
Called when a new attachment is created.  The *sender* object is the
new `Attachment`.  The user who created the attachment is passed in
the `user` kwarg.
""")

attachment_deleted = _signals.signal('attachment-deleted', """
Called when an attachment is deleted.  The *sender* object is the
`Attachment` that was deleted.  The user who deleted the attachment is
passed in the `user` kwarg.
""")

attachment_updated = _signals.signal('attachment-updated', """
Called when an attachment is updated.  The *sender* is the
`Attachment` that was updated.  The user who updated the attachment
is passed in the `user` kwarg.
""")

attachment_accessed = _signals.signal('attachment-accessed', """
Called when an attachment is accessed.  The *sender* is the
`Attachment` that was accessed.  The user who accessed the attachment
is passed in the `user` kwarg.  The `from_preview` kwarg will be set
to ``True`` if the download link on the preview page was used to access
the attachment or if the attachment was loaded to be displayed on the
preview page (opening the preview itself already sends this signal
with `from_preview=False`).
""")

get_file_previewers = _signals.signal('get-file-previewers', """
Expected to return one or more `Previewer` subclasses.
""")
