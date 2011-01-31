<!-- table which does the exterior border -->
<table width="98%" cellpadding="0" cellspacing="0" border="0" class="gestiontable">
	<tr>
		<td width="100%">
			<!-- interior table with all the heads-->
			<table width="100%" cellpadding="0" cellspacing="0" border="0" class="outervtab">
				<!-- Headers above "Abstract management" -->
				<%= context %>
				<!-- End of headers above "Abstract management" -->

				<!-- Header of "Abstract management" -->
				<tr>
					<td colspan="2" class="vtab">
						<table cellspacing="0" cellpadding="0" border="0" width="100%">
							<tr>
								<td width="<%= titleTabPixels %>px" class="vtabmenu" valign="top">
									<table cellpadding="0" cellspacing="0" border="0" width="<%= titleTabPixels %>px">
										<tr>
											<td align="right" class="menutitle"> <%= _("Abstract management")%></td>
										</tr>
									</table>
								</td>
								<td class="lastvtabtitle" width="100%">
									<%= title %>
								</td>
							</tr>
							<tr>
								<td colspan="3" class="lastvtab"><br></td>
							</tr>
						</table>
					</td>
				</tr>

				<!-- Close tags of the 2 upper headers -->
				<%= closeHeaderTags %>
				<!-- End of close tags of the 2 upper headers -->

				<!-- Intermediate tab -->
				<tr>
					<td colspan="2">
						<table cellspacing="0" cellpadding="0" border="0" width="100%" class="intermediatevtab">
							<tr>
								<td width="<%= intermediateVTabPixels %>px" align="left">
									<table class="intermediateleftvtab" width="<%= intermediateVTabPixels %>px" cellspacing="0" cellpadding="0" border="0">
										<tr><td>&nbsp;</td></tr>
									</table>
								</td>
							</tr>
							<tr>
								<td></td>
							</tr>
						</table>
					</td>
				</tr>
				<!-- End of intermediate tab -->
			<!-- End of interior table -->
			</table>
		</td>
	</tr>
	  <!-- End of header of "Abstract management" -->

 <!-- Body -->
	<tr>
		<td><%= body %><br></td>
	</tr>
 <!-- End of body -->

</table><!-- End of the table which does the exterior border -->