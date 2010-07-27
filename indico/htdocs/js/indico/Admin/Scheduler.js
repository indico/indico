type('TaskTable', ['RemoteTableWidget'],
     {
         _drawItem: function(pair) {
             var task = pair.get();

             // an 'element' is a tuple (ok, list) [timestamp, {...}],
             // where the second element is an object with the task attributes
             return [Html.td({}, task.id),
                     Html.td({}, task.typeId),
                     Html.td({}, Util.formatDateTime(task.startOn,
                                                     IndicoDateTimeFormats.Default)),
                     Html.td({}, Util.formatDateTime(task.createdOn,
                                                     IndicoDateTimeFormats.Default))];

         },

         _taskLine: function(task) {

         }
     },
     function(method) {
         this.RemoteTableWidget("schedTaskList", method, {})
     });

