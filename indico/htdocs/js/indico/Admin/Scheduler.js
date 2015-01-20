/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

type('TaskActions', [],
     {
         _request: function(method, args, success) {
             var killProgress =
                 IndicoUI.Dialogs.Util.progress($T("Executing Operation..."));

             indicoRequest(method, args,
                           function(result,error){
                               killProgress();
                               if(error) {
                                   IndicoUtil.errorReport(error);
                               } else {
                                   success(result);
                               }
                           });
         },

         deleteTask: function(task) {
             this._request('scheduler.tasks.delete',
                           {id: task.id},
                           function(result) {
                               // add some kind of decent notification bar?
                               new AlertPopup($T("Success"), $T("Task deleted.")).open();
                               this._table.refresh();
                           });
         },

         runFailedTask: function(task) {
             this._request('scheduler.tasks.runFailed',
                           {id: task.id},
                           function(result) {
                               // add some kind of decent notification bar?
                               new AlertPopup($T("Success"), $T("Task failed ran.")).open();
                               this._table.refresh();
                           });
         }

     },
     function(table) {
         this._table = table;
     });

type('TaskTable', ['RemoteTableWidget'],
     {
         draw: function() {
             return Html.div({},
                             this._drawToolbar(),
                             RemoteTableWidget.prototype.draw.call(this)
                            );
         },

         _drawItem: function(pair) {
             var task = pair.get();

             // an 'element' is a tuple (ok, list) [timestamp, {...}],
             // where the second element is an object with the task attributes
             return concat(this._taskLine(task),
                           [Html.td({},
                                    this._drawLineOptions(task))]);
         },

         _formatDateTime: function(dateTime, format){
             return Util.DateTime.friendlyDateTime(dateTime, format);
         },

         _taskLine: function(task) {
             return [Html.td({}, task.id),
                     Html.td({}, task.typeId),
                     Html.td({}, this._formatDateTime(task.startOn,
                                                      IndicoDateTimeFormats.Default)),
                     Html.td({}, this._formatDateTime(task.createdOn,
                                                      IndicoDateTimeFormats.Default))];
         },

         _drawToolbar: function() {
             var self = this;

             var refreshCount = $B(Html.span("smallGrey"),
                                   this._timeLeft,
                                   function(val) {
                                       return val + " " + $T("sec. left");
                                   });

             var chooser = new Chooser(
                 {
                     'stopMode': command(function() {
                         chooser.set('resumeMode');
                         clearTimeout(self._timeout);
                     }, $T('Stop monitoring')),
                     'resumeMode': command(function() {
                         chooser.set('stopMode');
                         self._timeout = setTimeout(
                             function() {
                                 self._countToRefresh(self._refreshTime);
                             }, 1000);
                     }, $T('Resume monitoring'))
                 });

             chooser.set('stopMode');

             return Html.div({style: {height: '50px'}},
                             Html.ul({className: "horizontalMenu",
                                      style: {cssFloat: 'left', height: '20px'}},
                                     Html.li({},
                                             Widget.link(chooser)),
                                     Html.li({}, Widget.link(command(function() {
                                         // do the actual refresh
                                         self.source.refresh();

                                         // reset refresh time counter
                                         self._timeLeft.set(self._refreshTime);
                                     }, $T('Refresh now')))),
                                     Html.li({}, refreshCount)),
                             Html.div({style:{cssFloat: 'left', marginTop: '4px',
                                              padding:'4px'}},
                                      this._progress));
         },

         _drawLineOptions: function() {
             return '';
         },

         // counting function
         _countToRefresh: function(refreshTime) {
             var self = this;
             var val = this._timeLeft.get();
             if (val > 1) {
                 this._timeLeft.set(val - 1)
             } else {
                 this._timeLeft.set(0);
                 this.refresh();
                 this._timeLeft.set(refreshTime);
             }
             // store the timeout reference, so that we can cancel it
             // when we switch tabs
             this._timeout = setTimeout(function() {
                 self._countToRefresh(refreshTime);
             }, 1000);
         },

         _runIndicator: function() {
             this._progress.dom.style.display = 'inline';
         },

         _stopIndicator: function() {
             this._progress.dom.style.display = 'none';
         },

         refresh: function() {
             this.source.refresh();
         }

     },
     function(method, args, refreshTime) {
         this._progress = progressIndicator(true);

         this._refreshTime = refreshTime || 5;
         this.RemoteTableWidget("schedTaskList", method, args || {});
         this._actions = new TaskActions(this);

         // counter till the next refresh
         this._timeLeft = new WatchValue(this._refreshTime);

         var self = this;
         this._timeout = setTimeout(function() {
             self._countToRefresh(self._refreshTime)
         }, 1000);

     });

type('FinishedTaskTable', ['TaskTable'],
     {

         _getHeader: function() {
             return Html.tr({},
                            Html.th({},'ID'),
                            Html.th({},'Task type'),
                            Html.th({},'Started on'),
                            Html.th({},'Ended on'),
                            Html.th({},'Creation date'),
                            Html.th({}, 'Options'));
         },

         _taskLine: function(task) {
             if (task._fossil == 'taskOccurrence') {
                 return [Html.td({}, task.task.id + ":" + task.id),
                         Html.td({}, task.task.typeId),
                         Html.td({}, this._formatDateTime(
                             task.startedOn,
                             IndicoDateTimeFormats.Default)),
                         Html.td({}, this._formatDateTime(
                             task.endedOn,
                             IndicoDateTimeFormats.Default)),
                         Html.td({}, this._formatDateTime(
                             task.task.createdOn,
                             IndicoDateTimeFormats.Default))];
             } else {
                 return [Html.td({}, task.id),
                         Html.td({}, task.typeId),
                         Html.td({}, this._formatDateTime(
                             task.startedOn,
                             IndicoDateTimeFormats.Default)),
                         Html.td({}, this._formatDateTime(
                             task.endedOn,
                             IndicoDateTimeFormats.Default)),
                         Html.td({}, this._formatDateTime(
                             task.createdOn,
                             IndicoDateTimeFormats.Default))];
             }
         }
     },
     function(method, criteria) {
         this.TaskTable(method, criteria, 30);
     });


type('FailedTaskTable', ['FinishedTaskTable'],
     {
         _runTask: function(task) {
             this._actions.runFailedTask(task);
         },

         _drawLineOptions: function(task) {
             var self = this;

             return task._fossil == 'taskOccurrence' ? '' :
                 Html.div({}, Widget.link(
                     command(
                         function() {
                             self._runTask(task);
                         }, "Run now")));
         }
     },
     function(method, criteria) {
         this.FinishedTaskTable(method, criteria);
     });


type('SchedulerSummaryWidget', ['RemoteWidget'],
     {
         drawContent: function() {
             var data = this.source.get();

             var state = Html.tr({},
                                 Html.td({}, $T('State')),
                                 Html.td({}, data.state ?
                                         Html.span({}, $T('Enabled')) :
                                         Html.span({}, $T('Disabled'))));

             var hostname = Html.tr({},
                                 Html.td({}, $T('Hostname')),
                                 Html.td({}, Html.span({}, data.state ? data.hostname : 'n/a')));
             var pid = Html.tr({},
                                 Html.td({}, $T('PID')),
                                 Html.td({}, Html.span({}, data.state ? data.pid : 'n/a')));


             var spool = Html.tr({}, Html.td({}, $T('Spooled commands')),
                                 Html.td({}, data.spooled));
             var queue = Html.tr({}, Html.td({}, $T('Queued tasks')),
                                 Html.td({}, data.waiting));
             var running = Html.tr({}, Html.td({}, $T('Running tasks')),
                                   Html.td({}, data.running));
             var failed = Html.tr({}, Html.td({}, $T('Failed tasks')),
                                  Html.td({}, data.failed));
             var finished = Html.tr({}, Html.td({}, $T('Finished tasks')),
                                  Html.td({}, data.finished));

             return Html.table({},
                               Html.tbody({}, state, hostname, pid, spool, queue, running, failed, finished));
         }
     },
     function(method) {
         this.RemoteWidget(method, {});
     });

type('WaitingTaskTable', ['TaskTable'],
     {
         _getHeader: function() {
             return Html.tr({},
                            Html.th({},'ID'),
                            Html.th({},'Task type'),
                            Html.th({},'Scheduled execution'),
                            Html.th({},'Creation date'),
                            Html.th({}, 'Options'));
         },

         _deleteTask: function(task) {
             this._actions.deleteTask(task);
         },

         _drawLineOptions: function(task) {
             var self = this;

             return Html.div({}, Widget.link(
                 command(
                     function() {
                         self._deleteTask(task);
                     }, "Delete")));
         }

     },
     function(method) {
         this.TaskTable(method, {}, 10);
     });

type('SchedulerPanel', ['JLookupTabWidget'],
     {
         _notifyTabChange: function() {
             // each time a tab changes, cancel the timeout events
             // (otherwise we'd have a circus of AJAX requests)
             if(this._currentWidget) {
                 clearTimeout(this._currentWidget._timeout);
             }
         },

         _summary: function() {
             return new SchedulerSummaryWidget('scheduler.summary');
         },

         _running: function() {
             return new TaskTable("scheduler.tasks.listRunning");
         },

         _waiting: function() {
             return new WaitingTaskTable("scheduler.tasks.listWaiting");
         },

         _history: function() {
             return new FinishedTaskTable("scheduler.tasks.listFinished",
                                          {'number': 10});
         },

         _failed: function() {
             return new FailedTaskTable("scheduler.tasks.listFailed",
                                        {'number': 10});
         },

         _keepStatusWrapper: function(func) {
             var self = this;
             return function() {
                 self._currentWidget = func();
                 return self._currentWidget.draw()
             }
         }

     }, function() {
         this.JLookupTabWidget([
             [$T('Summary'), this._keepStatusWrapper(this._summary)],
             [$T('Running Tasks'), this._keepStatusWrapper(this._running)],
             [$T('Waiting queue'), this._keepStatusWrapper(this._waiting)],
             [$T('Failed Tasks'), this._keepStatusWrapper(this._failed)],
             [$T('History'), this._keepStatusWrapper(this._history)]
         ]);
     });
