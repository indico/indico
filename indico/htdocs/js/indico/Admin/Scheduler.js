type('TaskTable', ['RemoteTableWidget'],
     {
         _drawItem: function(pair) {
             var elem = pair.get();
             alert(elem)
             return Html.td({}, elem);
         }
     },
     function(method) {
         this.RemoteTableWidget("schedTaskList", method, {})
     });