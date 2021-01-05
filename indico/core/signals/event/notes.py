# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


note_added = _signals.signal('note-added', """
Called when a note is added. The `sender` is the note.
""")

note_modified = _signals.signal('note-modified', """
Called when a note is modified. The `sender` is the note.
""")

note_deleted = _signals.signal('note-deleted', """
Called when a note is deleted. The `sender` is the note.
""")
