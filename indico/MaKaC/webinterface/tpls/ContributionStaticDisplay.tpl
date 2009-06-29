<table width="100%%" align="center">
    <tr>
        <td>
	    <table align="center" width="95%%" border="0" style="border: 1px solid #777777;">
            <tr><td>&nbsp;</td></tr>
            <tr>
                <td>
		            <table align="center" width="95%%" border="0">
		                <tr>
                            <td colspan="2" align="center"><font size="+1" color="black"><b>%(title)s</b></font></td>
		                </tr>
		                <tr>
		                    <td width="100%%" colspan="2">&nbsp;<td>
		                </tr>
		                <tr>
		                    <td colspan="2">
                                <table align="center">
                                    <tr>
                                        <td>
                                            <pre>%(description)s</pre>
                                        </td>
                                    </tr>
                                </table>
                            </td>
		                </tr>
		                <tr>
                		    <td width="100%%" colspan="2">&nbsp;<td>
                		</tr>
                		<tr>
                		    <td colspan="2">
                    		    <table align="center" width="90%%">
                        		    <tr>
                        		        <td align="right" valign="top" class="displayField"><b><%= _("Id")%>:</b></td>
                                        <td>%(id)s</td>
                                    </tr>
                        		    %(location)s
                        		    <tr>
                        		        <td align="right" valign="top" class="displayField"><b><%= _("Starting date")%>:</b></td>
                            			<td width="100%%">
                            			    <table cellspacing="0" cellpadding="0" align="left">
                                			    <tr>
                                			        <td align="right">%(startDate)s</td>
                                    				<td>&nbsp;&nbsp;%(startTime)s</td>
                                			    </tr>
                            			    </table>
                            			</td>
                        		    </tr>
                        		    <tr>
                    	    	        <td align="right" valign="top" class="displayField"><b><%= _("Duration")%>:</b></td>
                        	    		<td width="100%%">%(duration)s</td>
                        		    </tr>
                					%(contribType)s
				                	%(primaryAuthors)s
                					%(coAuthors)s
                                    %(speakers)s
                                    %(material)s
				                	<tr><td>&nbsp;</td></tr>
                                    %(inTrack)s
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        </td>
    </tr>
</table>
