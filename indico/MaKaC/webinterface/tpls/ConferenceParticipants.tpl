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
	if (!document.participantsForm.participants.length)	{
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
						<% if not nowutc() > self._conf.getStartDate(): %>
							<form action="<%= urlHandlers.UHConfModifParticipantsObligatory.getURL(self._conf) %>" method="post">
								Attendance to this event is 
									<select onchange="javascript:this.form.submit()">
										<option <% if self._conf.getParticipation().isObligatory(): %>selected<% end %>>mandatory</option>
										<option <% if not self._conf.getParticipation().isObligatory(): %>selected<% end %>>not mandatory</option>
									</select>
							</form>
						<% end %>
						<% else: %>
							The attendance to this event is 
								<% if self._conf.getParticipation().isObligatory(): %>
									<strong>mandatory</strong>
								<% end %>
								<% else: %>
									<strong>not mandatory</strong>
								<% end %>
						<% end %>      					
					</div>					

				</td>			
			</tr>-->
			<tr>			
				<td>
					<div>
						<% if not nowutc() > self._conf.getStartDate(): %>
							<form action="<%= urlHandlers.UHConfModifParticipantsAddedInfo.getURL(self._conf) %>" method="post">
								<%= _("When an event manager adds a participant, email notification will")%> 
									<select onchange="javascript:this.form.submit()">
										<option <% if self._conf.getParticipation().isAddedInfo(): %>selected<% end %>><%= _("be sent")%></option>
										<option <% if not self._conf.getParticipation().isAddedInfo(): %>selected<% end %>><%= _("not be sent")%></option>
									</select> <%= _("to the participant")%>
							</form>
						<% end %>
						<% else: %>
							<%= _("When an event manager adds a participant, email notification will")%> 
								<% if self._conf.getParticipation().isAddedInfo(): %>
									<strong><%= _("be sent")%></strong>
								<% end %>
								<% else: %>
									<strong><%= _("not be sent")%></strong>
								<% end %>							 
						<% end %>      					
					</div>		
				</td>			
			</tr>
			<tr>			
				<td><form action="<%= urlHandlers.UHConfModifParticipantsDisplay.getURL(self._conf) %>" method="post">
						<div>
							<%= _("The list of participants is")%>
								<select onchange="javascript:this.form.submit()">
									<option <% if self._conf.getParticipation().displayParticipantList(): %>selected<% end %>><%= _("displayed")%></option>
									<option <% if not self._conf.getParticipation().displayParticipantList(): %>selected<% end %>><%= _("not displayed")%></option>
								</select>
							<%= _("on the event page")%>        					
						</div>
					</form>
				</td>			
			</tr>			
			<tr>
				<td>					
					<div>
						<% if not nowutc() > self._conf.getStartDate(): %>
							<form action="<%= urlHandlers.UHConfModifParticipantsAllowForApplying.getURL(self._conf) %>" method="post">
								<%= _("Users")%>
									<select onchange="javascript:this.form.submit()">
										<option <% if self._conf.getParticipation().isAllowedForApplying(): %>selected<% end %>><%= _("may apply")%></option>
										<option <% if not self._conf.getParticipation().isAllowedForApplying(): %>selected<% end %>><%= _("may not apply")%></option>
									</select> <%= _("to participate in this event")%>
							</form>
						<% end %>
						<% else: %>
							<%= _("Users")%> 
								<% if self._conf.getParticipation().isAllowedForApplying(): %>
									<strong><%= _("may apply")%></strong>
								<% end %>
								<% else: %>
									<strong><%= _("may not apply")%></strong>
								<% end %> <%= _("to participate in this event")%>
						<% end %>      					
					</div>					
				</td>
			
			</tr>
            <tr>
                <td>                    
                    <div>
                        <% if not nowutc() > self._conf.getStartDate(): %>
                            <form action="<%= urlHandlers.UHConfModifParticipantsToggleAutoAccept.getURL(self._conf) %>" method="post">
                            <%= _("Participation requests")%> 
                                <select onchange="javascript:this.form.submit()" <% if not self._conf.getParticipation().isAllowedForApplying(): %>disabled="disabled"<%end%>>
                                    <option <% if self._conf.getParticipation().getAutoAccept(): %>selected<% end %><%= _(">are auto-approved")%></option>
                                    <option <% if not self._conf.getParticipation().getAutoAccept(): %>selected<% end %>><%= _("must be approved by the event managers (you)")%></option>
                                </select>
                            </form>
                        <% end %>
                        <% else: %>
                            <%= _("Participation requests")%> 
                                <% if self._conf.getParticipation().getAutoAccept(): %>
                                    <strong><%= _("are auto-approved")%></strong>
                                <% end %>
                                <% else: %>
                                    <strong><%= _("must be approved by the event managers (you)")%></strong>
                                <% end %>
                        <% end %>                       
                    </div>                  
                </td>
            </tr>
            
        	<% if self._conf.getParticipation().getPendingNumber() > 0 : %>            
                <tr>            		
                	<td>
                		<span style="color:green"><%= _("""Some users have applied for participation in this event. 
							See""")%> <a href="<%= urlHandlers.UHConfModifParticipantsPending.getURL(self._conf) %>"><%= _("pending participants")%></a>
						</span>
					</td>                 	
            	</tr>
			<% end %>
		</table>

		%(errorMsg)s
		%(infoMsg)s

		<table style="margin-top: 20px;">
				<tr>
					<td>Add participant: </td>
                    <td>
						<form action="<%= newParticipantURL %>" method="post">
								<div><input type="submit" value="<%= _("Define new")%>" class="btn"  /></div>
						</form>
					</td>
					
					<% if inviteAction: %>
					<td>
						
						<form action="%(inviteAction)s" method="post">
							<div>%(inviteButton)s</div>
						</form>
					</td>
					<% end %>

					<td>
						<form action="%(addAction)s" method="post">
							<div>%(addButton)s</div>
						</form>
					</td>

				</tr>
								
		</table>


		<div style="position: relative; overflow: auto; margin-top: 10px;">			
		<form action="%(statisticAction)s" method="post" id="statisticsForm"></form> 
			<form action="%(participantsAction)s" method="post" name="participantsForm">
		
				<div style="float: left; padding-right: 30px; min-width: 400px; min-height: 270px;">								
							<table>
								<tr>
									<th class="titleCellFormat">
										<img src="%(selectAll)s" alt="<%= _("Select all")%>" title="<%= _("Select all")%>" onclick="javascript:selectAll()">
										<img src="%(deselectAll)s" alt="<%= _("Deselect all")%>" title="<%= _("Deselect all")%>" onclick="javascript:deselectAll()">
										<%= _("Name")%>
									</th>
									<th class="titleCellFormat">&nbsp;<%= _("Status")%></th>
									<th class="titleCellFormat">&nbsp;<%= _("Presence")%></th>
								</tr>
									%(participants)s
								
				
							</table>				
				</div>

				<div style="padding-top: 30px;" class="uniformButtonVBar">
			                
                            <div><input type="button" class="btn" style="margin-bottom: 20px" value="<%= _("View attendance") %>" onclick="javascript:$E('statisticsForm').dom.submit();" /></div>
                        
							<% if presenceButton: %>
								<div>%(presenceButton)s</div>
							<% end %>
							
							<% if absenceButton: %>
								<div>%(absenceButton)s</div>
							<% end %>
							
							<% if askButton: %>
								<div>%(askButton)s</div>
							<% end %>
							
							<% if excuseButton: %>
								<div>%(excuseButton)s</div>
							<% end %>
							
							<% if sendButton: %>
								<div style="margin-bottom: 20px">%(sendButton)s</div>
							<% end %>
							
							<% if sendAddedInfoButton: %>
								<div>%(sendAddedInfoButton)s</div>
							<% end %>
                            <div>%(excelButton)s</div>
							<div>%(removeButton)s</div>
				
				</div>
				
		
			</form>
		</div>		
		
		
