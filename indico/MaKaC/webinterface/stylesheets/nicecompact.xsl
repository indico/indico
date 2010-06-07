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

<xsl:stylesheet version='1.0' xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:import href="include/date.xsl"/>
<xsl:import href="include/common.xsl"/>
<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">

<table width="100%" bgcolor="white">
<tr>
	<td>
	<b>

    <xsl:call-template name="displayModifIcons">
        <xsl:with-param name="item" select="."/>
        <xsl:with-param name="confId" select="/iconf/ID"/>
        <xsl:with-param name="sessId" value=""/>
        <xsl:with-param name="sessCode" value=""/>
        <xsl:with-param name="contId" value=""/>
        <xsl:with-param name="subContId" value=""/>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
    </xsl:call-template>

	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	</b><br/>

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
              </xsl:if> </b>
              to <b>
              <xsl:call-template name="prettydate">
                <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
              </xsl:call-template>
              <xsl:if test="substring(./endDate,12,5) != '00:00'">
                (<xsl:value-of select="substring(./endDate,12,5)"/>)
              </xsl:if> </b>
            </xsl:otherwise>
            </xsl:choose>
	<br/><br/>
	</td>
	<td align="right">
	<table border="0" bgcolor="silver" cellspacing="3" cellpadding="1">
	<tr><td>
		<table border="0" bgcolor="white" cellpadding="2" cellspacing="0" width="100%">
		<tr>
			<td>

			<table><tr><td bgcolor="#90c0f0"><font size="-2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></font></td><td><font size="-2"><b>: Sessions</b></font></td></tr></table>

			</td>
			<td>

			<table cellspacing="0"><tr><td bgcolor="silver"><font size="-2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></font></td><td><font size="-2">/</font></td><td bgcolor="#D2D2D2"><font size="-2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></font></td><td><font size="-2"><b>: Talks</b></font></td></tr></table>

			</td>
			<td>

			<table><tr><td bgcolor="#FFcccc"><font size="-2"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text></font></td><td><font size="-2"><b>: Breaks</b></font></td></tr></table>

			</td>
		</tr>
		</table>
	</td></tr>
	</table>
	</td>
</tr>
</table>

<center>
<table cellspacing="1" cellpadding="0" bgcolor="white" border="0">

<tr>
<td></td>
<xsl:for-each select="./session|./contribution|./break">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:if test="count(preceding::session[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(startDate,0,11)=$day]) = 0">
	<td class="headerselected" align="center" bgcolor="#000060"><font size="-2" color="white">
	<b>
	<xsl:call-template name="prettydate">
		<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
	</xsl:call-template>
	</b><br/>
	</font></td>
</xsl:if>
</xsl:for-each>
</tr>

<tr bgcolor="white">
<td valign="top" class="headerselected" bgcolor="#000060" width="30">
	<table width="100%" cellspacing="0" cellpadding="2" border="0">
	<tr>
	<td align="center" class="headerselected" bgcolor="#000060">
	<font size="-2" color="white"><b>
	AM
	</b></font>
	</td>
	</tr>
	</table>
</td>



<xsl:for-each select="./session|./contribution|./break">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:if test="count(preceding::session[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(startDate,0,11)=$day]) = 0">
	<td valign="top" bgcolor="gray">
	<xsl:if test="count(/iconf/session[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13]|/iconf/contribution[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13]|/iconf/break[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13])>0">
	<table width="100%" cellspacing="1" cellpadding="3" border="0">
	<xsl:for-each select="/iconf/session[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13]|/iconf/contribution[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13]|/iconf/break[substring(startDate,0,11)=$day and substring(startDate,12,2) &lt; 13]">
	<xsl:apply-templates select="."/>
	</xsl:for-each>
	</table>
	</xsl:if>
	</td>
</xsl:if>
</xsl:for-each>
</tr>



<tr>
<td valign="top" class="headerselected" bgcolor="#000060">
	<table width="100%" cellspacing="0" cellpadding="2" border="0">
	<tr>
	<td align="center" class="headerselected" bgcolor="#000060">
	<font size="-2" color="white"><b>
	PM
	</b></font>
	</td>
	</tr>
	</table>
</td>


<xsl:for-each select="./session|./contribution|./break">
<xsl:variable name="day" select="substring(./startDate,0,11)"/>
<xsl:if test="count(preceding::session[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::contribution[position()=1 and substring(startDate,0,11)=$day]) = 0 and count(preceding::break[position()=1 and substring(startDate,0,11)=$day]) = 0">
	<td valign="top" bgcolor="gray">
	<xsl:if test="count(/iconf/session[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13]|/iconf/contribution[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13]|/iconf/break[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13])>0">
	<table width="100%" cellspacing="1" cellpadding="3" border="0">
	<xsl:for-each select="/iconf/session[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13]|/iconf/contribution[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13]|/iconf/break[substring(startDate,0,11)=$day and substring(startDate,12,2) &gt;= 13]">
	<xsl:apply-templates select="."/>
	</xsl:for-each>
	</table>
	</xsl:if>
	</td>
</xsl:if>
</xsl:for-each>
</tr>
</table>
</center>

</xsl:template>

<xsl:template match="session">
	<tr>
	<td valign="top" bgcolor="#b0e0ff" width="5%">
	<b><font size="-2"><xsl:value-of select="substring(./startDate,12,5)"/></font></b>
	</td>
	<td colspan="1" bgcolor="#90c0f0"><font size="-2">

      <xsl:call-template name="displayModifIcons">
        <xsl:with-param name="item" select="."/>
        <xsl:with-param name="confId" select="../ID"/>
        <xsl:with-param name="sessId" select="./ID"/>
        <xsl:with-param name="sessCode" select="./code"/>
        <xsl:with-param name="contId">null</xsl:with-param>
        <xsl:with-param name="subContId">null</xsl:with-param>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.session</xsl:with-param>
      </xsl:call-template>

	<b><xsl:value-of select="./title" disable-output-escaping="yes"/></b>
	<xsl:if test="count(child::convener/user) != 0">
	<font size="-2">-<font color="green" size="-2">
	<xsl:apply-templates select="./convener"/>
	</font></font>
	</xsl:if>
	<xsl:if test="substring(./endDate,12,5) != '00:00'">
		(until <xsl:value-of select="substring(./endDate,12,5)"/>)
	</xsl:if>
    <xsl:if test="count(./location) != 0 and normalize-space(string(../location)) != normalize-space(string(./location))">
      (<xsl:apply-templates select="./location"><xsl:with-param name="span">author</xsl:with-param></xsl:apply-templates>)
    </xsl:if>
	<xsl:if test="count(child::material) != 0">
	<xsl:for-each select="./material">
	<xsl:apply-templates select="."><xsl:with-param name="sessionId" select="./ID"/></xsl:apply-templates>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:for-each>
	</xsl:if>
	</font></td>
	</tr>
	<xsl:for-each select="./contribution|./break">
	<xsl:apply-templates select=".">
	<xsl:with-param name="ids" select="../ID"/>
	</xsl:apply-templates>
	</xsl:for-each>
</xsl:template>

<xsl:template match="contribution">
  <xsl:param name="ids" select="0"/>
  <xsl:choose>
  <xsl:when test="count(preceding::contribution) mod 2 = 1">
  <xsl:text disable-output-escaping="yes">
  &#60;tr bgcolor="silver"&#62;
  </xsl:text>
  </xsl:when>
  <xsl:otherwise>
  <xsl:text disable-output-escaping="yes">
  &#60;tr bgcolor="#D2D2D2"&#62;
  </xsl:text>
  </xsl:otherwise>
  </xsl:choose>
    <xsl:choose>
    <xsl:when test="count(preceding::contribution) mod 2 = 1">
    <xsl:text disable-output-escaping="yes">
    &#60;td bgcolor="#D0D0D0" valign="top" width="5%"&#62;
    </xsl:text>
    </xsl:when>
    <xsl:otherwise>
    <xsl:text disable-output-escaping="yes">
    &#60;td bgcolor="#E2E2E2" valign="top" width="5%"&#62;
    </xsl:text>
    </xsl:otherwise>
    </xsl:choose>
      <font size="-2"><xsl:value-of select="substring(./startDate,12,5)"/></font>
    <xsl:text disable-output-escaping="yes">&#60;/td&#62;</xsl:text>
    <td valign="top">
      <font size="-2">

        <xsl:if test="name(..) = 'session'">
        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../ID"/>
          <xsl:with-param name="sessId" select="../ID"/>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
        <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>
          </xsl:if>
          <xsl:if test="name(..) != 'session'">
        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../ID"/>
          <xsl:with-param name="sessId">null</xsl:with-param>
          <xsl:with-param name="contId" select="./ID" />
          <xsl:with-param name="subContId">null</xsl:with-param>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.contribution</xsl:with-param>
        </xsl:call-template>
        </xsl:if>

      <xsl:value-of select="./title" disable-output-escaping="yes"/>
      <xsl:if test="count(child::speakers) != 0">
      <font size="-2"> -<font color="green" size="-2">
      <xsl:apply-templates select="./speakers"/>
      </font></font>
      </xsl:if>
      <xsl:if test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">
      <font size="-2">(
      <xsl:apply-templates select="./location"/>
      )</font>
      </xsl:if>
      <xsl:if test="count(child::material) != 0">
      <xsl:for-each select="./material">
      <xsl:apply-templates select="."><xsl:with-param name="contribId" select="../ID"/><xsl:with-param name="sessionId" select="$ids"/></xsl:apply-templates>
      <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
      </xsl:for-each>
      </xsl:if>
      </font>
    </td>
  <xsl:text disable-output-escaping="yes">&#60;/tr&#62;</xsl:text>
</xsl:template>


<xsl:template match="break">
  <tr>
    <td valign="top" bgcolor="#FFdcdc">
      <font size="-2"><xsl:value-of select="substring(./startDate,12,5)"/></font>
    </td>
    <td valign="top" bgcolor="#FFcccc" align="center" colspan="1">
      <font size="-2">

      <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
      </xsl:call-template>

      ---<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><xsl:value-of select="./name"/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>---
      </font>
    </td>
  </tr>
</xsl:template>


</xsl:stylesheet>
