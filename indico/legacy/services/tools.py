# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


def toJsDate(datetime):
    return "(new Date(%i,%i,%i,%i,%i,%i))" % (datetime.year,
                                              datetime.month - 1,
                                              datetime.day,
                                              datetime.hour,
                                              datetime.minute,
                                              datetime.second)
