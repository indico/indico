
type("MeetingParticipantsListManager", [], {

    searchUser: function(action) {
        var self = this;
        var chooseUsersPopup = new ChooseUsersPopup($T('Add participant(s)'), true, null, false, true, false, false, true,
            function(userList) {
                var killProgress = IndicoUI.Dialogs.Util.progress();
                // send the request
                indicoRequest('event.participant.addExistingParticipant',
                              {confId: self.confId, action: action, userList: userList},
                              function(result, error) {
                                  if (!error) {
                                      self._updateParticipantsTable(result);
                                      killProgress();
                                  } else {
                                      killProgress();
                                      IndicoUtil.errorReport(error);
                                  }
                              }
                );
            }
        );
        chooseUsersPopup.execute();
    },

    defineNew: function() {
        var self = this;
        var newUser = $O();
        var newUserPopup = new UserDataPopup(
                $T('Define new'),
                newUser,
                function(newData) {
                    if (newUserPopup.parameterManager.check()) {
                        var killProgress = IndicoUI.Dialogs.Util.progress();
                        indicoRequest('event.participant.addNewParticipant',
                                      {confId: self.confId, userData: newData},
                                      function(result, error) {
                                          if (!error) {
                                              self._updateParticipantsTable(result);
                                              killProgress();
                                          } else {
                                              killProgress();
                                              IndicoUtil.errorReport(error);
                                          }
                                      }
                        );
                        newUserPopup.close();
                    }
                }, false, false, false, false);
        newUserPopup.open();
    },

    _updateParticipantsTable: function(result) {
        // Clean previous table
        var self = this;
        this.table.set('');
        var tbody = Html.tbody({});
        this.table.append(tbody);
        var tr = Html.tr();
        var td;
        var input;
        var span;
        var urlEdit;
        var link;

        // Add the header
        var th = Html.th({className: 'titleCellFormat'});
        tr.append(th);
        var imgSelectAll = Html.img({
            src: this.selectAllSrc,
            alt: $T('Select all '),
            title: $T('Select all '),
            style: {paddingRight:'4px'}
        });
        imgSelectAll.observeClick(function() {self.selectAll();});
        th.append(imgSelectAll);

        var imgDeselectAll = Html.img({
            src: this.deselectAllSrc,
            alt: $T('Deselect all '),
            title: $T('Deselect all '),
            style: {paddingRight:'4px'}
        });
        imgDeselectAll.observeClick(function() {self.deselectAll();});
        th.append(imgDeselectAll);
        span = Html.span({}, $T('Name'));
        th.append(span);
        th = Html.th({className:'titleCellFormat'}, $T(' Status'));
        tr.append(th);
        th = Html.th({className:'titleCellFormat'}, $T(' Presence'));
        tr.append(th);
        tbody.append(tr);

        // Add the rows of the table
        for (var i=0; i<result.length; i++) {
            tr = Html.tr();
            td = Html.td({className: 'abstractDataCell'});
            tr.append(td);
            input = Html.input('checkbox', {name: 'participants'}, result[i]['id']);
            td.append(input);

            urlEdit = this.editUrl + '&participantId=' + result[i]['id'];
            link = Html.a({href: urlEdit, className:'fakeLink'}, ' ' + result[i]['title'] + ' ' + result[i]['name']);
            td.append(link);

            td = Html.td({className: 'abstractDataCell'}, result[i]['status']);
            tr.append(td);
            td = Html.td({className: 'abstractDataCell'}, result[i]['presenceText']);
            tr.append(td);
            tbody.append(tr);
        }
    },

    selectAll: function() {
        if (!document.participantsForm.participants.length){
            document.participantsForm.participants.checked=true
        } else {
            for (i = 0; i < document.participantsForm.participants.length; i++) {
                document.participantsForm.participants[i].checked=true
            }
        }
    },

    deselectAll: function() {
        if (!document.participantsForm.participants.length)    {
            document.participantsForm.participants.checked=false
        } else {
           for (i = 0; i < document.participantsForm.participants.length; i++) {
               document.participantsForm.participants[i].checked=false
           }
        }
    }

},

    function (confId, table, editUrl, selectAllSrc, deselectAllSrc) {
        this.confId = confId;
        this.table = table;
        this.editUrl = editUrl;
        this.selectAllSrc = selectAllSrc;
        this.deselectAllSrc = deselectAllSrc;
    }
);
