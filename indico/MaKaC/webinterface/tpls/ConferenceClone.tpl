<script type="text/javascript">	
        var date = new Date();
	var dateOnce = IndicoUI.Widgets.Generic.dateField_sdate(false,Util.formatDateTime(date, IndicoDateTimeFormats.DefaultHourless),['stddo', 'stdmo', 'stdyo'])
	var dateInterval_start = IndicoUI.Widgets.Generic.dateField(false,null,['inddi', 'indmi', 'indyi'])
	var dateInterval_until = IndicoUI.Widgets.Generic.dateField(false,null,['stddi', 'stdmi', 'stdyi'])
	var dateDays_start = IndicoUI.Widgets.Generic.dateField(false,null,['inddd', 'indmd', 'indyd'])
	var dateDays_until = IndicoUI.Widgets.Generic.dateField(false,null,['stddd', 'stdmd', 'stdyd'])


	function setCloneType(type)	{
			document.getElementById('ct').value = type
			$E('cloningForm').dom.submit()
		}
	
	function cloneOnceForm()
	{
		
		var isValid = dateOnce.processDate();
		
		if (isValid == true)
		{
			setCloneType('once');
		}
		
	}

	function cloneIntervalForm()
	{
		
		var isValid = dateInterval_start.processDate() && dateInterval_until.processDate();
		
		if (isValid == true)
		{
			setCloneType('intervals');
		}
		
	}
	
	function cloneDaysForm()
	{
		
		var isValid = dateDays_start.processDate() && dateDays_until.processDate();
		
		if (isValid == true)
		{
			setCloneType('days');
		}
		
	}

	
	window.onload = function()
	{
		   	
		$E('cloneOncePlace').addContent(dateOnce);
		$E('cloneIntervalPlace_start').addContent(dateInterval_start);
		$E('cloneIntervalPlace_until').addContent(dateInterval_until);		
		$E('cloneDaysPlace_start').addContent(dateDays_start);
		$E('cloneDaysPlace_until').addContent(dateDays_until);
	};
</script>


<h3 class="formTitle"><%= _("Clone the conference :")%> %(confTitle)s</h3>


<form id="cloningForm" action="%(cloning)s" method="post">							
     
	<div style="padding:10px; border:1px solid #5294CC; background:#F6F6F6; width: 400px;">
		<input type="hidden" id="ct" name="cloneType" value="none" />
		<ul style="list-style-type: none;">
			<li><strong><%= _("Choose elements to clone:")%></strong></li>
			
			<li><input type="checkbox" name="cloneDetails" id="cloneDetails" checked disabled value="1"/>
				<%= _("Main information")%></li>
			<li><input type="checkbox" name="cloneMaterials" id="cloneMaterials" value="1"/>
				<%= _("Attached materials")%></li>
			<li><input type="checkbox" name="cloneAccess" id="cloneAccess" value="1" checked />
				<%= _("Access and management privileges")%></li>
			<li><input type="checkbox" name="cloneAlerts" id="cloneAlerts" checked value="1" />
				<%= _("Alerts")%></li>

			%(cloneOptions)s
		</ul>				
	</div>
			
	<div style="margin-top: 10px; margin-bottom: 10px;">
		<%= _("You have the possibility to: clone the event")%> <a href="#cloneOnce"><%= _("once")%></a>, 
		<%= _("clone it")%> <a href="#cloneInterval"><%= _("using a specific interval")%></a> <%= _("or")%> 
		<a href="#cloneDays"><%= _("specific days")%></a>. 
	</div>
			
	<div class="optionGroup">				
				<h3 class="groupTitleSmall"><a name="cloneOnce"></a><%= _("Clone the event only once at the specified date")%></h3>

				<span id="cloneOncePlace">
						<input type="hidden" id="stddo" name="stddo"/>
						<input type="hidden" id="stdmo" name="stdmo"/>
						<input type="hidden" id="stdyo" name="stdyo"/>
				</span>							
                           
				<input type="button" class="btn" name="cloneOnce" value="<%= _("clone once")%>" 
								onclick="javascript:cloneOnceForm();" />
	</div>

	<div class="optionGroup">				
				<h3 class="groupTitleSmall"><a name="cloneInterval"></a><%= _("Clone the event with a fixed interval:")%></h3>
			
					<div class="formLine">
						<label for="period"> <%= _("every:")%> </label>
						<input type="text" size="3" name="period" id="period" value="1" />
							<small>
								<select name="freq">
									<option value="day"><%= _("day(s)")%></option>
									<option value="week" selected><%= _("week(s)")%></option>
									<option value="month"><%= _("month(s)")%></option>
									<option value="year"><%= _("year(s)")%></option>
								</select>
							</small>
					</div>
					<div class="formLine">
						<label> <%= _("starting:")%> </label>
						<span id="cloneIntervalPlace_start">
							<input type="hidden" id="inddi" name="inddi"/>
							<input type="hidden" id="indmi" name="indmi"/>
							<input type="hidden" id="indyi" name="indyi"/>
						</span>
					</div>
					<div class="formLine">
						<input type="radio" name="func" value="until" checked />
													
						<label> <%= _("until:")%> </label>
						<span id="cloneIntervalPlace_until">
							<input type="hidden" id="stddi" name="stddi"/>
							<input type="hidden" id="stdmi" name="stdmi"/>
							<input type="hidden" id="stdyi" name="stdyi"/>							
						</span>	
						<small> <%= _("(inclusive)")%> </small>
						
					</div>
					<div class="formLine">
						<input type="radio" name="func" value="ntimes" />													
						<input type="text" name="numi" id="numi" size="3" value="1" />
						<label for="numi"> <%= _("time(s)")%></label>
					</div>
					<div>
						<input 	type="button" class="btn" name="cloneWithInterval" value="<%= _("clone with interval")%>" 
								onclick="javascript:cloneIntervalForm();" />
					</div>
		</div>
		<div class="optionGroup">						
				<h3 class="groupTitleSmall"><a name="cloneDays"></a><%= _("Clone the agenda on given days:")%></h3>

				<div class="formLine">
				    <label> <%= _("on the:")%> </label>
				    <select name="order">
			            <option value="1"><%= _("first")%></option>
			            <option value="2"><%= _("second")%></option>
			            <option value="3"><%= _("third")%></option>
			            <option value="4"><%= _("fourth")%></option>
			            <option value="last"><%= _("last")%></option>
			        </select>
			        <select name="day">
			            <option value="0"><%= _("Monday")%></option>
			            <option value="1"><%= _("Tuesday")%></option>
			            <option value="2"><%= _("Wednesday")%></option>
			            <option value="3"><%= _("Thursday")%></option>
			            <option value="4"><%= _("Friday")%></option>
			            <option value="5"><%= _("Saturday")%></option>
			            <option value="6"><%= _("Sunday")%></option>
			            <option value="NOVAL" disabled>---------------</option>
			            <option value="OpenDay"><%= _("Open Day")%></option>
			        </select>
				        <label for="monthPeriod"> <%= _("every")%> </label>
				        <input type="text" size="3" id="monthPeriod" name="monthPeriod" value="1" />
				        <label for="monthPeriod"> <%= _("month(s)")%></label>				        
				</div>
			    <div class="formLine">      
			      <label><%= _("starting:")%>&nbsp;</label>
			      <span id="cloneDaysPlace_start">
							<input type="hidden" id="inddd" name="inddd"/>
							<input type="hidden" id="indmd" name="indmd"/>
							<input type="hidden" id="indyd" name="indyd"/>			      	
			      </span>					      				  
				</div>
				<div class="formLine">			       
			   		<input type="radio" name="func" value="until" checked />
			      	<label><%= _("until:")%>&nbsp;</label>
			        <span id="cloneDaysPlace_until">
							<input type="hidden" id="stddd" name="stddd"/>
							<input type="hidden" id="stdmd" name="stdmd"/>
							<input type="hidden" id="stdyd" name="stdyd"/>										        	
			        </span>
			        <small> <%= _("(inclusive)")%></small>
			    </div>
				<div class="formLine">
			      <input type="radio" name="func" value="ntimes" />
			      <input type="text" name="numd" size="3" value="1" />
			      <label> <%= _("time(s)")%></label>
			   	</div>
			   
				<input 	type="button" class="btn" name="cloneGivenDays" value="<%= _("clone given days")%>" 
									onclick="javascript:cloneDaysForm();" />

		</div>

</form>

