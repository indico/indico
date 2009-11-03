
var Util = {
    parseId: function(id){

        /* Returns the type and the split ids for a provided composite id */

        var m = id.match(/^(?:([^\.]+)\.)?s(\d+)$/);
        if (m) {
            return concat(["Session"], m.slice(1));
        }

        m = id.match(/^(?:([^\.]+)\.)s(\d+)\.(\d+)$/);
        if (m) {
            return concat(["SessionSlot"], m.slice(1));
        }

        m = id.match(/^(?:([^\.]+)\.)(\d+)$/);
        if (m) {
            return concat(["Contribution"], m.slice(1));
        }

        return concat(["Conference"], [id]);
    }
};

var IndicoSortCriteria = {
    StartTime: function(c1, c2) {
        return SortCriteria.Integer(c1.startDate.time.replaceAll(':',''),
                                    c2.startDate.time.replaceAll(':',''));
    }
};