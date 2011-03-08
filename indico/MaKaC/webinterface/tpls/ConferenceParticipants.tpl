<% from MaKaC.common.timezoneUtils import nowutc %>
<script type="text/javascript">
<!--
function selectAll()
{
    //document.participantsForm.trackShowNoValue.checked=true
    if (!document.participantsForm.participants.length){
        document.participantsForm.participants.checked=true
    } else {
        for (i = 0; i < document.participantsForm.participants.length; i++) {
            document.participantsForm.participants[i].checked=true
        }
    }
}

function deselectAll()
{
    //document.participantsForm.trackShowNoValue.checked=false
    if (!document.participantsForm.participants.length)    {
        document.participantsForm.participants.checked=false
    } else {
       for (i = 0; i < document.participantsForm.participants.length; i++) {
           document.participantsForm.participants[i].checked=false
       }
    }
}
//-->
</script>


        <table>
            <!-- <tr>
                <td>
                    <div>
                        % if not nowutc() > self_._conf.getStartDate(): 
                            <form action="${ urlHandlers.UHConfModifParticipantsObligatory.getURL(self_._conf) }" method="post">
                                Attendance to this event is
                                    <select onchange="javascript:this.form.submit()">
                                        <option ${"selected" if self_._conf.getParticipation().isObligatory() else ""}>mandatory</option>
                                        <option ${"selected" if not self_._conf.getParticipation().isObligatory() else ""}>not mandatory</option>
                                    </select>
                            </form>
                        % else: 
                            The attendance to this event is&nbsp;
                                % if self_._conf.getParticipation().isObligatory(): 
                                    <strong>mandatory</strong>
                                % else: 
                                    <strong>not mandatory</strong>
                                % endif
                        % endif
                    </div>

                </td>
            </tr>-->
            <tr>
                <td>
                    <div>
                        % if not nowutc() > self_._conf.getStartDate(): 
                            <form action="${ urlHandlers.UHConfModifParticipantsAddedInfo.getURL(self_._conf) }" method="post">
                                ${ _("When an event manager adds a participant, email notification will")}
                                    <select onchange="javascript:this.form.submit()">
                                        <option ${"selected" if self_._conf.getParticipation().isAddedInfo() else ""}>${ _("be sent")}</option>
                                        <option ${"selected" if not self_._conf.getParticipation().isAddedInfo() else ""}>${ _("not be sent")}</option>
                                    </select> ${ _("to the participant")}
                            </form>
                        % else: 
                            ${ _("When an event manager adds a participant, email notification will")}&nbsp;
                                % if self_._conf.getParticipation().isAddedInfo(): 
                                    <strong>${ _("be sent")}</strong>
                                % else: 
                                    <strong>${ _("not be sent")}</strong>
                                % endif
                        % endif
                    </div>
                </td>
            </tr>
            <tr>
                <td><form action="${ urlHandlers.UHConfModifParticipantsDisplay.getURL(self_._conf) }" method="post">
                        <div>
                            ${ _("The list of participants is")}
                                <select onchange="javascript:this.form.submit()">
                                    <option ${"selected" if self_._conf.getParticipation().displayParticipantList() else ""}>${ _("displayed")}</option>
                                    <option ${"selected" if not self_._conf.getParticipation().displayParticipantList() else ""}>${ _("not displayed")}</option>
                                </select>
                            ${ _("on the event page")}
                        </div>
                    </form>
                </td>
            </tr>
            <tr>
                <td>
                    <div>
                        % if not nowutc() > self_._conf.getStartDate(): 
                            <form action="${ urlHandlers.UHConfModifParticipantsAllowForApplying.getURL(self_._conf) }" method="post">
                                ${ _("Users")}
                                    <select onchange="javascript:this.form.submit()">
                                        <option ${"selected" if self_._conf.getParticipation().isAllowedForApplying() else ""}>${ _("may apply")}</option>
                                        <option ${"selected" if not self_._conf.getParticipation().isAllowedForApplying() else ""}>${ _("may not apply")}</option>
                                    </select> ${ _("to participate in this event")}
                            </form>
                        % else: 
                            ${ _("Users")}&nbsp;
                                % if self_._conf.getParticipation().isAllowedForApplying(): 
                                    <strong>${ _("may apply")}</strong>
                                % else: 
                                    <strong>${ _("may not apply")}</strong>
                                % endif
 ${ _("to participate in this event")}
                        % endif
                    </div>
                </td>

            </tr>
            <tr>
                <td>
                    <div>
                        % if not nowutc() > self_._conf.getStartDate(): 
                            <form action="${ urlHandlers.UHConfModifParticipantsToggleAutoAccept.getURL(self_._conf) }" method="post">
                            ${ _("Participation requests")}
                                <select onchange="javascript:this.form.submit()" ${'disabled="disabled"' if not self_._conf.getParticipation().isAllowedForApplying() else ""}>
                                    <option ${"selected" if self_._conf.getParticipation().getAutoAccept() else ""}${ _(">are auto-approved")}</option>
                                    <option ${"selected" if not self_._conf.getParticipation().getAutoAccept() else ""}>${ _("must be approved by the event managers (you)")}</option>
                                </select>
                            </form>
                        % else: 
                            ${ _("Participation requests")}&nbsp;
                                % if self_._conf.getParticipation().getAutoAccept(): 
                                    <strong>${ _("are auto-approved")}</strong>
                                % else: 
                                    <strong>${ _("must be approved by the event managers (you)")}</strong>
                                % endif
                        % endif
                    </div>
                </td>
            </tr>

               % if self_._conf.getParticipation().getPendingNumber() > 0 : 
                <tr>
                    <td>
                          <span style="color:green">${ _("""Some users have applied for participation in this event.
                            See""")} <a href="${ urlHandlers.UHConfModifParticipantsPending.getURL(self_._conf) }">${ _("pending participants")}</a>
                        </span>
                    </td>
                </tr>
            % endif
        </table>

        ${ errorMsg }
        ${ infoMsg }

        <table style="margin-top: 20px;">
                <tr>
                    <td>Add participant: </td>

                    <td>
                        <form action="${ addAction }" method="post">
                            <div>${ addButton }</div>
                        </form>
                    </td>

                    <td>
                        <form action="${ newParticipantURL }" method="post">
                                <div><input type="submit" value="${ _("Define new")}" class="btn"  /></div>
                        </form>
                    </td>

                    % if inviteAction: 
                    <td>

                        <form action="${ inviteAction }" method="post">
                            <div>${ inviteButton }</div>
                        </form>
                    </td>
                    % endif

                </tr>

        </table>


        <div style="position: relative; overflow: auto; margin-top: 10px;">
        <form action="${ statisticAction }" method="post" id="statisticsForm"></form>
            <form action="${ participantsAction }" method="post" name="participantsForm">

                <div style="float: left; padding-right: 30px; min-width: 400px; min-height: 270px;">
                            <table>
                                <tr>
                                    <th class="titleCellFormat">
                                        <img src="${ selectAll }" alt="${ _("Select all")}" title="${ _("Select all")}" onclick="javascript:selectAll()">
                                        <img src="${ deselectAll }" alt="${ _("Deselect all")}" title="${ _("Deselect all")}" onclick="javascript:deselectAll()">
                                        ${ _("Name")}
                                    </th>
                                    <th class="titleCellFormat">&nbsp;${ _("Status")}</th>
                                    <th class="titleCellFormat">&nbsp;${ _("Presence")}</th>
                                </tr>
                                    ${ participants }


                            </table>
                </div>

                <div style="padding-top: 30px;" class="uniformButtonVBar">

                            <div><input type="button" class="btn" style="margin-bottom: 20px" value="${ _("View attendance") }" onclick="javascript:$E('statisticsForm').dom.submit();" /></div>

                            % if presenceButton: 
                                <div>${ presenceButton }</div>
                            % endif

                            % if absenceButton: 
                                <div>${ absenceButton }</div>
                            % endif

                            % if askButton: 
                                <div>${ askButton }</div>
                            % endif

                            % if excuseButton: 
                                <div>${ excuseButton }</div>
                            % endif

                            % if sendButton: 
                                <div style="margin-bottom: 20px">${ sendButton }</div>
                            % endif

                            % if sendAddedInfoButton: 
                                <div>${ sendAddedInfoButton }</div>
                            % endif
                            <div>${ excelButton }</div>
                            <div>${ removeButton }</div>

                </div>


            </form>
        </div>

