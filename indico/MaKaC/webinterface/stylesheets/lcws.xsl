<?xml version='1.0'?>
<!--

     This file is part of CDS Indico.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.

     CDS Indico is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     CDS Indico is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
-->

<xsl:stylesheet version='1.0'
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:include href="include/date.xsl"/>
<xsl:include href="include/common.xsl"/>
<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">
<table width="100%" border="0" cellpadding="0" cellspacing="0">
  <tr>
    <td height="298" align="center" valign="top">      <p><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></p>
      <table width="90%" border="0" cellpadding="0" cellspacing="0" class="headerabstract">

        <tr>
          <td colspan="3"><table width="100%" border="0" cellpadding="0" cellspacing="0" class="headerselected2">
            <tr>
              <td width="14%"><img src="images/smallLCWS.png" width="113" height="69"/></td>
              <td width="57%">
                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>
		<span class="titles"><xsl:text disable-output-escaping="yes">&#38;quot;</xsl:text><xsl:value-of select="./title" disable-output-escaping="yes"/><xsl:text disable-output-escaping="yes">&#38;quot;</xsl:text></span><br/>
		<xsl:if test="count(child::chair/user) != 0">
                        <span class="author">chaired by
			<xsl:apply-templates select="./chair"/>
			</span>
		</xsl:if>
	      </td>
              <td width="9%" class="settings"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></td>
              <td width="20%" nowrap="1" class="settings">
            <xsl:choose>
            <xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
              <b>
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
              </xsl:call-template>
              </b>
              <xsl:if test="substring(./startDate,12,5) != '00:00'">
                from <b><xsl:value-of select="substring(./startDate,12,5)"/></b>
              </xsl:if>
              <xsl:if test="substring(./endDate,12,5) != '00:00'">
                to <b><xsl:value-of select="substring(./endDate,12,5)"/></b>
              </xsl:if>
            </xsl:when>
            <xsl:otherwise>
              from <b>
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./startDate,12,5) != '00:00'">
                (<xsl:value-of select="substring(./startDate,12,5)"/>)
              </xsl:if> </b><br/>
              to <b>
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./endDate,12,5) != '00:00'">
                (<xsl:value-of select="substring(./endDate,12,5)"/>)
              </xsl:if> </b>
            </xsl:otherwise>
            </xsl:choose>

		<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
			<br/>at
			<xsl:apply-templates select="./location"/>
		</xsl:if>
		<xsl:if test="./announcer/user/name/@first != ''">
			<br/>announced by:
                        <xsl:apply-templates select="./announcer"/>
		</xsl:if>
 </td>

            </tr>
          </table></td>
        </tr>

	<xsl:if test="./description != ''">
        <tr>
          <td valign="top" nowrap="1" class="abstract"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></td>
          <td valign="top" nowrap="1" class="abstract"><strong>Description :</strong></td>
          <td valign="top" width="82%" class="abstract">
		<xsl:value-of select="./description" disable-output-escaping="yes"/>
	  </td>
        </tr>
	</xsl:if>

	<xsl:if test="./participants != ''">
        <tr>
          <td valign="top" nowrap="1" class="abstract"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></td>
          <td valign="top" nowrap="1" class="abstract"><strong>Participants :</strong></td>
          <td valign="top" width="82%" class="abstract">
			<xsl:value-of select="./participants" disable-output-escaping="yes"/>
		  </td>
        </tr>
	</xsl:if>


	<xsl:if test="count(./material) != 0">
        <tr class="headerselected2">
          <td width="6%" height="33" valign="top" nowrap="1" class="headerselectedimg"><img src="images/paperclip.png" width="56" height="32"/></td>
          <td valign="top" nowrap="1" class="headerselected3"><strong>Material
            :</strong></td>
          <td valign="top" nowrap="1" class="headerselected3"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:for-each select="./material">
			<xsl:if test="./type!='part1' and ./type!='part2' and ./type!='part3' and ./type!='part4' and ./type!='part5' and ./type!='part6' and ./type!='part7' and ./type!='part8' and ./type!='part9' and ./type!='part10'">
			<xsl:apply-templates select="."/>
			</xsl:if>
		</xsl:for-each>
		<div align="right">
		<xsl:for-each select="./material">
			<xsl:if test="./type='part1' or ./type='part2' or ./type='part3' or ./type='part4' or ./type='part5' or ./type='part6' or ./type='part7' or ./type='part8' or ./type='part9' or ./type='part10'">
				<a href="{./url}" class="material">
				<img src="images/{./type}.png" class="parts"/>
				</a><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
			</xsl:if>
		</xsl:for-each>
		</div>

	  </td>
        </tr>
	</xsl:if>

	<tr class="headerselected2">
          <td valign="top" nowrap="1" class="headertimetable" colspan="2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></td>
          <td valign="top" width="82%" class="headertimetable">
		<div align="right">
		<xsl:for-each select="./session|./contribution|./break">
			<xsl:variable name="day" select="substring(./startDate,0,11)"/>
			<xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
				<small><a href="#{$day}"><font size="-3"><xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template></font></a>
				|
				</small>
			</xsl:if>
		</xsl:for-each>
		</div>
	  </td>
	</tr>


	<tr class="headertimetable">
	<td colspan="3">

	<xsl:for-each select="./session|./contribution|./break">
	<xsl:variable name="ids" select="./ID"/>
	<xsl:variable name="day" select="substring(./startDate,0,11)"/>

	<xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
		<br/>
		<table style="padding-left:5pt;" width="100%"><tr><td>
		<b>
		<span class="day">
		<xsl:call-template name="prettydate">
			<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
		</xsl:call-template>
		</span>
		</b>
		</td><td align="right">
		<a href="#top">top<img src="images/upArrow.png" border="0" style="vertical-align:middle"/></a>
		<a name="{$day}"/>
		</td></tr></table>
	</xsl:if>

	<xsl:apply-templates select="."/>
	</xsl:for-each>

	</td>
	</tr>

      	</table>
    <div align="center"></div>
    </td>
  </tr>
</table>

</xsl:template>



<xsl:template match="session">
	<br/>
	<table width="100%" cellpadding="1" cellspacing="0" border="0" style="padding-left: 20pt; padding-right:2pt;">
	<tr>
	<a name="{./ID}"/>
	<td valign="top" class="headersession">
		<span class="sessiontime">
		<xsl:if test="substring(./startDate,12,5) != '00:00'"><xsl:value-of select="substring(./startDate,12,5)"/></xsl:if>
		<xsl:if test="substring(./endDate,12,5) != '00:00'"><i>-&gt;<xsl:value-of select="substring(./endDate,12,5)"/></i></xsl:if>
		</span>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>
		<span class="sessiontitle">
		<xsl:value-of select="./title"/>
		</span>
	<xsl:if test="count(child::convener/user) != 0">
		(Convener:
		<xsl:apply-templates select="./convener"/>
		)
	</xsl:if>
	<xsl:if test="count(child::location/name) != 0">
		(Location:
		<xsl:apply-templates select="./location"/>
		)
	</xsl:if>
	<xsl:if test="count(child::material) != 0">
		<xsl:for-each select="./material">
		<xsl:apply-templates select="."><xsl:with-param name="sessionId" select="../ID"/></xsl:apply-templates>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		</xsl:for-each>
	</xsl:if>
	<xsl:if test="./description != ''">
		<br/>
		<xsl:value-of select="./description" disable-output-escaping="yes"/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:if>
	</td>
	<td align="right">
		<a href="http://polywww.in2p3.fr/actualites/congres/lcws2004/"><font color="green">Main conference page</font></a>
	</td>
	</tr>
	<xsl:if test="count(child::contribution)+count(child::break) != 0">
	<tr>
	<td colspan="2">
	<table width="100%" cellpadding="0" cellspacing="0" border="0">
	<xsl:for-each select="./contribution|./break">
	<tr>
		<xsl:apply-templates select="."/>
	</tr>
	</xsl:for-each>
	</table>
	</td></tr>
	</xsl:if>
	</table>
</xsl:template>



<xsl:template match="contribution">
	<xsl:variable name="idt" select="./ID"/>
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;table width="100%" cellpadding="0" cellspacing="0" border="0" style="padding-left: 20pt; padding-right:2pt;"&#62;&#60;tr&#62;</xsl:text>
	</xsl:if>
	<xsl:choose>
	<xsl:when test="count(preceding::contribution) mod 2 = 1">
		<xsl:text disable-output-escaping="yes">
		&#60;td colspan="2"  valign="top"&#62;
		&#60;table width="100%" cellpadding="" cellspacing="0" border="0" class="headertalk"&#62;
		</xsl:text>
	</xsl:when>
	<xsl:otherwise>
		<xsl:text disable-output-escaping="yes">
		&#60;td colspan="2" valign="top"&#62;
		&#60;table width="100%" cellpadding="0" cellspacing="0" border="0" class="headertalklight"&#62;
		</xsl:text>
	</xsl:otherwise>
	</xsl:choose>

	<tr>
		<td align="right" valign="top" width="1%" class="headers">
		<xsl:if test="substring(./startDate,12,5) != '00:00'">
			<xsl:value-of select="substring(./startDate,12,5)"/>
		</xsl:if>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:if test="./broadcasturl != ''">
			<br/><a href="{./broadcasturl}">
			(video broadcast)</a>
		</xsl:if>
		</td>

		<td valign="top" class="headers">
		<xsl:if test="./category != '' and ./category != ' '">
			<span class="headerselected"><xsl:value-of select="./category"/></span>
			<br/>
		</xsl:if>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>
		<xsl:value-of select="./title" disable-output-escaping="yes"/>
		<xsl:if test="./duration != '00:00'"><small><font color="red"> (<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>) </font></small></xsl:if>
		<xsl:if test="./repno != ''">
			(<xsl:value-of select="./repno" disable-output-escaping="yes"/>)
		</xsl:if>
		<xsl:if test="count(child::material) != 0">
			(<xsl:for-each select="./material">
			<xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/></xsl:apply-templates>
			<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
			</xsl:for-each>)
		</xsl:if>
		<xsl:if test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">
		(<xsl:if test="./location/name != '' and ./location/name != ../location/name"><xsl:value-of select="./location/name"/><br/></xsl:if>
		<xsl:if test="./location/room != '0--' and ./location/room != ../location/room and ./location/room != ''"><xsl:value-of select="./location/room" disable-output-escaping="yes"/></xsl:if>)
		</xsl:if>

		</td>

		<td align="right" class="headers">
		<xsl:if test="count(child::speakers) != 0">
			<xsl:apply-templates select="./speakers"/>
		</xsl:if>
		</td>
	</tr>

	<xsl:if test="./abstract != ''">
	<tr>
		<td></td>
		<td colspan="2" class="headers">
		<xsl:value-of select="./abstract" disable-output-escaping="yes"/>
		</td>
	</tr>
	</xsl:if>

	<xsl:for-each select="subcontribution">
		<xsl:apply-templates select="."/>
	</xsl:for-each>

	<xsl:text disable-output-escaping="yes">&#60;/table&#62;&#60;/td&#62;</xsl:text>
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;/tr&#62;</xsl:text>
	<xsl:text disable-output-escaping="yes">&#60;/table&#62;</xsl:text>
	</xsl:if>
</xsl:template>



<xsl:template match="subcontribution">
	<xsl:variable name="idt" select="./ID"/>
	<tr>
		<td></td>
		<td valign="top">
		<ul>
		<li>

                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>
		<small>
		<xsl:value-of select="./title" disable-output-escaping="yes"/>
		</small>

		<xsl:if test="./duration != '00:00'">
			<small><font color="red"> (<xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template>) </font></small>
		</xsl:if>

		<xsl:if test="@repno != ''">
			(<xsl:value-of select="@repno" disable-output-escaping="yes"/>)
		</xsl:if>

		<xsl:if test="count(child::material) != 0">
			(<xsl:for-each select="./material">
			<xsl:apply-templates select="."><xsl:with-param name="contribId" select="../../ID"/><xsl:with-param name="subContId" select="../ID"/></xsl:apply-templates>
			<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
			</xsl:for-each>)
		</xsl:if>

		<xsl:if test="./description != ''">
			<br/><small><xsl:value-of select="./description" disable-output-escaping="yes"/></small>
		</xsl:if>

		</li>
		</ul>

		</td>

		<td align="right">
		<xsl:if test="count(child::speakers) != 0">
			<xsl:apply-templates select="./speakers"/>
		</xsl:if>
		</td>
	</tr>
</xsl:template>




<xsl:template match="break">
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;table cellpadding="0" cellspacing="0" border="0" width="100%" style="padding-left: 20pt; padding-right:2pt;"&#62;</xsl:text>
	</xsl:if>
		<tr>
		<td align="right" valign="top" width="1%" class="headerbreak">
		<xsl:if test="substring(./startDate,12,5) != '00:00'">
			<xsl:value-of select="substring(./startDate,12,5)"/>
		</xsl:if>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:if test="./broadcasturl != ''">
			<br/><a href="{./broadcasturl}">
			<br/>(video broadcast)</a>
		</xsl:if>
		</td>
		<td colspan="2" class="headerbreak">
			<center>
			<xsl:value-of select="./name" disable-output-escaping="yes"/>
			</center>
		</td>
		</tr>
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;/table&#62;</xsl:text>
	</xsl:if>
</xsl:template>




<xsl:template match="chair|announcer">
	<xsl:for-each select="./user">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span">author</xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling::user) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>




<xsl:template match="convener|speakers">
	<xsl:for-each select="./user">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling::user) != 0">,<xsl:text disable-output-escaping="yes"> </xsl:text></xsl:if>
	</xsl:for-each>
</xsl:template>



</xsl:stylesheet>
