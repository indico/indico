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

<xsl:include href="include/date.xsl"/>
<xsl:include href="include/common.xsl"/>

<xsl:output method="html"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">

<table width="650" align="center">
<tr>
<td>

<div align="right">
<font face="Times">
<xsl:for-each select="./repno">
<xsl:apply-templates select="."/><br/>
</xsl:for-each>
 <xsl:call-template name="prettydate">
	<xsl:with-param name="dat" select="./modified"/>
</xsl:call-template>
</font>

</div>

<br/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><br/>

<center>
<b>
<font size="+1" face="arial">
ORGANISATION EUROP<xsl:text disable-output-escaping="yes">&#38;Eacute;</xsl:text>ENNE POUR LA RECHERCHE NUCL<xsl:text disable-output-escaping="yes">&#38;Eacute;</xsl:text>AIRE<br/>
<font size="+3" face="arial">
CERN
</font>
EUROPEAN ORGANIZATION FOR NUCLEAR RESEARCH
</font>
</b>
</center>

<center>
<hr width="50%"/>
</center>

<br/><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text><br/>

<center>
<font size="+1" face="Times">
<u>
<xsl:value-of select="./category1" disable-output-escaping="yes"/><br/>
</u>
</font>



<xsl:call-template name="displayModifIcons">
    <xsl:with-param name="item" select="."/>
    <xsl:with-param name="confId" select="/iconf/ID"/>
    <xsl:with-param name="sessId" value=""/>
    <xsl:with-param name="contId" value=""/>
    <xsl:with-param name="subContId" value=""/>
    <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
</xsl:call-template>

<font size="+1" face="Times">
<xsl:value-of select="./title" disable-output-escaping="yes"/><br/>
</font>

<font size="+1" face="Times">
<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
	<xsl:apply-templates select="./location"/>
</xsl:if> -
<xsl:choose>
<xsl:when test="substring(./startDate,0,11) = substring(./endDate,0,11)">
  <xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template>
  <xsl:if test="substring(./startDate,12,5) != '00:00'">
	- <u><xsl:value-of select="substring(./startDate,12,5)"/></u>
  </xsl:if>
</xsl:when>
<xsl:otherwise>
    from
    <xsl:call-template name="prettydate">
    <xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
    </xsl:call-template>
    (<xsl:value-of select="substring(./startDate,12,5)"/>)
    to
    <xsl:call-template name="prettydate">
    <xsl:with-param name="dat" select="substring(./endDate,0,11)"/>
    </xsl:call-template>
    (<xsl:value-of select="substring(./endDate,12,5)"/>)
</xsl:otherwise>
</xsl:choose>
</font>
<br/>
<xsl:if test="count(child::material) != 0">
    <xsl:for-each select="./material">
      <font face="Times" size="+1"><a href="{./displayURL}">
            <xsl:value-of select="./title"/>
            </a></font>
            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    </xsl:for-each>
  </xsl:if>
<br/>

<font size="+1" face="Times">
<b>
<xsl:choose>
	<xsl:when test="./status = 'close'">
		FINAL AGENDA
	</xsl:when>
	<xsl:when test="./status = 'open'">
		DRAFT AGENDA
	</xsl:when>
</xsl:choose>
</b>
</font>

</center>
<xsl:if test="./description != ''">
	<br/><br/>
	<i>Description: </i><br/>
        <xsl:apply-templates select="./description"/>
</xsl:if>
<xsl:if test="./participants != ''">
	<br/><br/>
	<i>Participants: </i><br/>
	<xsl:value-of select="./participants" disable-output-escaping="yes"/>
</xsl:if>
<br/><br/>

<table width="100%" border="0" cellspacing="5">
<xsl:for-each select="./session|./contribution|./break">
  <xsl:apply-templates select="."/>
</xsl:for-each>
</table>
<br/>

</td>
</tr>
</table>
</xsl:template>

<xsl:template match="session">
  <xsl:variable name="ids" select="./ID"/>
  <xsl:if test="count(/iconf/session) != 1">
  <tr>
  <td colspan="4" align="left"><br/>
  <font face="Times" size="+1">
  <b>

  <xsl:call-template name="displayModifIcons">
      <xsl:with-param name="item" select="."/>
      <xsl:with-param name="confId" select="../ID"/>
	<xsl:with-param name="sessId" select="./ID"/>
	<xsl:with-param name="contId">null</xsl:with-param>
	<xsl:with-param name="subContId">null</xsl:with-param>
	<xsl:with-param name="uploadURL">Indico.Urls.UploadAction.session</xsl:with-param>
  </xsl:call-template>

  <xsl:value-of select="./title" disable-output-escaping="yes"/>
  </b>
  <xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
    <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    (<xsl:apply-templates select="./location"/>)
  </xsl:if>

  <br/>
  <xsl:if test="count(child::material) != 0">
    <xsl:for-each select="./material">
      <font face="Times" size="+1"><a href="{./displayURL}">
            <xsl:value-of select="./title"/>
            </a></font>
            <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
    </xsl:for-each>
  </xsl:if>

  <hr width="100%"/>
  <xsl:if test="./description != '' and ./description!=' '">
	<xsl:value-of select="./description" disable-output-escaping="yes"/>
	<hr width="100%"/>
  </xsl:if>
  </font>
  </td>
  </tr>
  </xsl:if>
  <xsl:for-each select="./contribution|./break">
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<xsl:template match="contribution">
<xsl:variable name="idt" select="./ID"/>
	<xsl:variable name="day" select="substring(./startDate,0,11)"/>
	<xsl:if test="count(preceding-sibling::contribution[position()=1 and substring(./startDate,0,11)=$day]) = 0">
	<tr>
	        <td colspan="2" valign="top"><font face="Times">
	        <i>
		<xsl:call-template name="prettydate">
			<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
		</xsl:call-template>
	        </i>
	        <br/><br/>
	        </font></td>
		<td align="right" valign="top"><font face="Times">
		<u>Documents</u>
		</font><br/><br/></td>
	</tr>
	</xsl:if>
<tr><td colspan="3"></td></tr>
<tr>
        <td valign="top">
	<xsl:choose>
	<xsl:when test="/iconf/type != 'olist'">
	        <b>
	        <xsl:if test="substring(./startDate,12,5) != '00:00'">
	                <font face="times" size="+1"><xsl:value-of select="substring(./startDate,12,5)"/></font>
	        </xsl:if>
	        </b>
	</xsl:when>
	<xsl:otherwise>
		<font face="times" size="+1"><xsl:number from="agenda" level="any" format="1. "/></font>
	</xsl:otherwise>
	</xsl:choose>
        </td>

	<td valign="top">

	<xsl:if test="./category != ''">
		<font face="times" size="+1">
		<xsl:value-of select="./category"/>
		</font>
		<br/>
	</xsl:if>
	<font face="times" size="+1">
	<xsl:value-of select="./title" disable-output-escaping="yes"/>
	</font>
	<br/>
        <xsl:if test="./abstract != ''">
	<br/><font face="times" size="+1">
        <xsl:apply-templates select="./abstract"/></font><br/>
	</xsl:if>
	</td>

	<td align="right" valign="top" nowrap="1">
	<xsl:if test="count(child::speakers) != 0">
		<xsl:apply-templates select="./speakers"/>
                <br/>
	</xsl:if>
    <xsl:if test="count(child::material) != 0">
        <xsl:for-each select="./material">
          <font face="Times" size="+1"><a href="{./displayURL}">
                <xsl:value-of select="./title"/>
                </a></font>
                <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
        </xsl:for-each>
    </xsl:if>
    </td>
    <td valign="top">
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
	</td>
</tr>
<xsl:for-each select="./subcontribution">
  <xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>

<xsl:template match="subcontribution">
<xsl:variable name="idt" select="./id"/>
<tr>
	<td>
	</td>
	<td valign="top">
	<table width="100%">
	<tr>
	<td valign="top" width="10pt">
		<font face="times" size="+0"><xsl:number from="contribution" level="any" format="a. "/></font>
	</td>
	<td valign="top">

	<xsl:if test="./category != ''">
		<B>
		<xsl:value-of select="./category"/>
		</B>:
	</xsl:if>
	<font face="times" size="+0"><xsl:value-of select="./title" disable-output-escaping="yes"/></font>
	</td>
	</tr>
	</table>
	</td>
	<td align="right" valign="top">
	<xsl:if test="count(child::speakers) != 0">
		<xsl:apply-templates select="./speakers"/>
                <br/>
	</xsl:if>
	<xsl:if test="count(child::material) != 0">
        <xsl:for-each select="./material">
          <font face="Times" size="+1"><a href="{./displayURL}">
                <xsl:value-of select="./title"/>
                </a></font>
                <xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
        </xsl:for-each>
    </xsl:if>
	</td>
    <td>
        <xsl:if test="name(../..) = 'session'">
        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../../ID"/>
          <xsl:with-param name="sessId" select="../../ID"/>
          <xsl:with-param name="contId" select="../ID" />
          <xsl:with-param name="subContId" select="./ID"/>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
        </xsl:call-template>
          </xsl:if>
          <xsl:if test="name(../..) != 'session'">
        <xsl:call-template name="displayModifIcons">
          <xsl:with-param name="item" select="."/>
          <xsl:with-param name="confId" select="../../ID"/>
          <xsl:with-param name="sessId">null</xsl:with-param>
          <xsl:with-param name="contId" select="../ID" />
          <xsl:with-param name="subContId" select="./ID"/>
          <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.subContribution</xsl:with-param>
        </xsl:call-template>
        </xsl:if>
    </td>
</tr>
</xsl:template>


<xsl:template match="break">
<tr>
	<td colspan="3" align="center">

          <xsl:call-template name="displayModifIcons">
              <xsl:with-param name="item" select="."/>
          </xsl:call-template>

	<font face="Times" size="+1">--- <xsl:value-of select="./name" disable-output-escaping="yes"/> ---</font>
	</td>
</tr>
</xsl:template>

<xsl:template match="chair|announcer">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span">author</xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

<xsl:template match="convener|speakers">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

<xsl:template match="user">
	<xsl:param name="span"/>
	<xsl:apply-templates select="./name"/>
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
	</a>
	<xsl:if test="count(following-sibling::material) != 0">; </xsl:if>
</xsl:template>

</xsl:stylesheet>
