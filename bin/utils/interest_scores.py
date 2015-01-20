import sys
from pprint import pprint

from MaKaC.common import DBMgr
from MaKaC.user import AvatarHolder

from indico.util.suggestions import get_category_scores, update_event_data, iter_interesting_events

with DBMgr.getInstance().global_connection():
    # 44 is jb
    # 22116 is pedro
    # 42604 is me (adrian)
    avatar = AvatarHolder().getById(sys.argv[1] if len(sys.argv) > 1 else '42604')
    pprint(dict((' -> '.join(c.getCategoryPathTitles()), score)
                for c, score in get_category_scores(avatar, True).iteritems()))
    data = {}
    for categ, score in get_category_scores(avatar).iteritems():
        if score > 0:
            update_event_data(avatar, categ, data)
    if data:
        for event in iter_interesting_events(avatar, data):
            print repr(event)
