<?xml version='1.0'?>
<!-- $Id: standardconf.xsl,v 1.9 2008/08/13 13:31:23 jose Exp $

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


	<tr class="headerselected2">
          <td valign="top" nowrap="1" class="headertimetable4" colspan="2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></td>
          <td valign="top" width="82%" class="headertimetable4">
		<div align="right">
		<font size="-3">
		<xsl:for-each select="./session|./contribution|./break">
			<xsl:variable name="day" select="substring(./startDate,0,11)"/>
			<xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
				<small><a href="#{$day}"><xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template></a>
				|
				</small>
			</xsl:if>
		</xsl:for-each>
		</font>
		</div>
	  </td>
	</tr>


	<tr class="headertimetable">
	<td colspan="3">

	<xsl:for-each select="./session|./contribution|./break">
	<xsl:variable name="ids" select="./ID"/>
	<xsl:variable name="day" select="substring(./startDate,0,11)"/>

	<xsl:if test="count(preceding::session[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(./startDate,0,11)=$day]) = 0">
		<br/><br/>
		<xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#60;/tr&#62;</xsl:text>
		<xsl:text disable-output-escaping="yes">&#60;tr&#62;</xsl:text>
		<td valign="top" align="right" colspan="2" class="headertimetable4">
		<b>
		<span class="day">
		<xsl:call-template name="prettydate">
			<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
		</xsl:call-template>
		</span>
		</b>
		<br/>
		<a href="#top">top<img src="images/upArrow.png" border="0" style="vertical-align:middle"/></a>
		</td>
		<xsl:text disable-output-escaping="yes">&#60;td class="headertimetable2"&#62;</xsl:text>
		<a name="{$day}"/>
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
	<table width="100%" cellpadding="1" cellspacing="0" border="0">
	<tr>
	<a name="{./ID}"/>
	<td valign="top" class="headersession">
		<span class="sessiontime">
		<xsl:if test="substring(./startDate,12,5) != '00:00'"><xsl:value-of select="substring(./startDate,12,5)"/></xsl:if>
		<xsl:if test="substring(./endDate,12,5) != '00:00'"><i>-&gt;<xsl:value-of select="substring(./endDate,12,5)"/></i></xsl:if>
		</span>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
                <xsl:call-template name="displayModifIcons">
                    <xsl:with-param name="item" select="."/>
                </xsl:call-template>
		<span class="sessiontitle">
		<xsl:value-of select="./title"/>
		</span>
	<xsl:if test="count(child::convener) != 0">
		(Convener:
		<xsl:apply-templates select="./convener"/>
		)
	</xsl:if>
	<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
		(Location:
		<xsl:apply-templates select="./location"/>
		)
	</xsl:if>
	<xsl:if test="count(child::material) != 0">
		<xsl:for-each select="./material">
		<xsl:apply-templates select="."><xsl:with-param name="sessionId" select="./ID"></xsl:with-param></xsl:apply-templates>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		</xsl:for-each>
	</xsl:if>
	<xsl:if test="./description != ''">
		<br/>
		<xsl:value-of select="./description" disable-output-escaping="yes"/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:if>
	</td>
	</tr>
	</table>
	<xsl:if test="count(child::contribution) != 0">
	<table width="100%" cellpadding="4" cellspacing="0" border="0">
	<tr>
	<xsl:for-each select="contribution|break">
		<xsl:apply-templates select="."/>
	</xsl:for-each>
	</tr>
	</table>
	</xsl:if>
</xsl:template>



<xsl:template match="contribution">
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;table width="100%" cellpadding="4" cellspacing="0" border="0"&#62;</xsl:text>
	</xsl:if>
	<xsl:choose>
	<xsl:when test="count(preceding::contribution) mod 2 = 1">
		<xsl:text disable-output-escaping="yes">
		&#60;td colspan="2" width="75%" valign="top" class="headertalk"&#62;
		&#60;table width="100%" cellpadding="0" cellspacing="0" border="0" class="headertalk"&#62;
		</xsl:text>
	</xsl:when>
	<xsl:otherwise>
		<xsl:text disable-output-escaping="yes">
		&#60;td colspan="2" width="75%" valign="top" class="headertalklight"&#62;
		&#60;table width="100%" cellpadding="0" cellspacing="0" border="0" class="headertalklight"&#62;
		</xsl:text>
	</xsl:otherwise>
	</xsl:choose>

	<tr>
		<td align="center" valign="top" width="1%">
		<xsl:if test="substring(./startDate,12,5) != '00:00'">
			<xsl:value-of select="substring(./startDate,12,5)"/>
		</xsl:if>
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
		<xsl:if test="./broadcasturl != ''">
			<br/><a href="{./broadcasturl}">
			(video broadcast)</a>
		</xsl:if>
		</td>

		<td valign="top">
		<xsl:if test="./category != '' and ./category != ' '">
			<span class="headerselected"><xsl:value-of select="./category"/></span>
			<br/>
		</xsl:if>
		<xsl:variable name="idt" select="./ID"/>
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
			<xsl:apply-templates select="."><xsl:with-param name="sessionId" select="./ID"></xsl:with-param></xsl:apply-templates>
			<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
			</xsl:for-each>)
		</xsl:if>
		</td>

		<xsl:choose>
		<xsl:when test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">
		<td align="center" valign="top" bgcolor="#90C0F0" width="1%">
		<xsl:if test="./location/name != '' and ./location/name != ../location/name"><xsl:value-of select="./location/name"/><br/></xsl:if>
		<xsl:if test="./location/room != '0--' and ./location/room != ../location/room and ./location/room != ''"><xsl:value-of select="./location/room" disable-output-escaping="yes"/></xsl:if>
		</td>
		</xsl:when>
		<xsl:otherwise>
		<td width="1%" align="center" valign="top"></td>
		</xsl:otherwise>
		</xsl:choose>

		<td align="right">
		<xsl:if test="count(child::speakers) != 0">
			<xsl:apply-templates select="./speakers"/>
		</xsl:if>
		</td>
	</tr>

	<xsl:if test="./abstract != ''">
	<tr>
		<td></td>
		<td colspan="2">
		<xsl:value-of select="./abstract" disable-output-escaping="yes"/>
		</td>
	</tr>
	</xsl:if>

	<xsl:for-each select="subcontribution">
		<xsl:apply-templates select="."/>
	</xsl:for-each>

	<xsl:text disable-output-escaping="yes">&#60;/table&#62;&#60;/td&#62;</xsl:text>
	<xsl:text disable-output-escaping="yes">&#60;/tr&#62;</xsl:text>
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;/table&#62;</xsl:text>
	</xsl:if>
</xsl:template>



<xsl:template match="subcontribution">
	<xsl:variable name="idt" select="./ID"/>
	<tr>
		<td colspan="2">
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
			<xsl:apply-templates select="."><xsl:with-param name="sessionId" select="./ID"></xsl:with-param></xsl:apply-templates>
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

		<xsl:if test="count(child::speaker) != 0">
			(<xsl:apply-templates select="./speaker"/>)
		</xsl:if>

		</td>
	</tr>
</xsl:template>




<xsl:template match="break">
	<xsl:if test="name(..)='iconf'">
	<xsl:text disable-output-escaping="yes">&#60;table cellpadding="4" cellspacing="0" border="0" width="100%"&#62;</xsl:text>
	</xsl:if>
		<tr>
		<td align="center" valign="top" width="1%" class="headerbreak">
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
	<xsl:if test="count(following-sibling::user) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

<xsl:template match="user">
	<xsl:param name="span"/>
	<span class="author"><xsl:apply-templates select="./name"/></span>
	<xsl:if test="./organization != ''">
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>(<i><xsl:value-of select="./organization" disable-output-escaping="yes"/></i>)
	</xsl:if>
</xsl:template>

<xsl:template match="name">
	<xsl:value-of select="./@first" disable-output-escaping="yes"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="./@last" disable-output-escaping="yes"/>
</xsl:template>

<xsl:template match="location">
	<b><xsl:value-of select="./name"/></b>
	<xsl:if test="./room != '0--' and ./room != 'Select:'">
		(
		<xsl:value-of select="./room" disable-output-escaping="yes"/>
		)
	</xsl:if>
</xsl:template>

<xsl:template match="material">
	<xsl:param name="sessionId"/>
	<xsl:param name="contribId"/>
	<a href="{./displayURL}" class="material">
	<img src="images/smallpaperclip.png" border="0"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="./type"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="./title"/>
	</a>
	<xsl:if test="count(following-sibling::material) != 0">; </xsl:if>
</xsl:template>



</xsl:stylesheet>
