<!-- table which does the exterior border -->
<table width="98%%" cellpadding="0" cellspacing="0" border="0" class="gestiontable">
	<tr>
		<td width="100%%">
			<!-- interior table with all the heads-->
			<table width="100%%" cellpadding="0" cellspacing="0" border="0" class="outervtab">

				<!-- Headers above "Notification Template" -->
				%(context)s
				<!-- End of headers above "Notification Template" -->
      
				<!-- Header of "Notification Template" -->
				<tr>
					<td colspan="2" class="vtab">
						<table cellspacing="0" cellpadding="0" border="0" width="100%%">
							<tr>
								<td width="%(titleTabPixels)spx" class="vtabmenu" valign="top">
									<table cellpadding="0" cellspacing="0" border="0" width="%(titleTabPixels)spx">
										<tr>
											<td width="27px">&nbsp;</td>
											<td align="right" class="menutitle"> <%= _("Notification TPL")%></td>
										</tr>
									</table>
								</td>
								<td class="lastvtabtitle" width="100%%">
									%(title)s
								</td>
							</tr>
							<tr>
								<td colspan="3" class="lastvtab"><br></td>
							</tr>
						</table>
					</td>
				</tr>
	  <!-- End of header of "Notification Template" -->
	  
	  <!-- Close tags of the upper header -->
				%(closeHeaderTags)s
	  <!-- End of close tags of the upper header -->

      <!-- Intermediate tab -->
				<tr>
					<td colspan="2">
						<table cellspacing="0" cellpadding="0" border="0" width="100%%" class="intermediatevtab">
							<tr>
								<td width="%(intermediateVTabPixels)spx" align="left">
									<table class="intermediateleftvtab" width="%(intermediateVTabPixels)spx" cellspacing="0" cellpadding="0" border="0">
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

			</table><!-- End of interior table -->
		</td>
	</tr>

 <!-- Body -->
	<tr>
		<td>%(body)s<br></td>
	</tr>
 <!-- End of body -->

</table><!-- End of the table which does the exterior border -->