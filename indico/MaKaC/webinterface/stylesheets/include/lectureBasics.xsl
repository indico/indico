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





<xsl:template name="eventInfoBox">
    <div class="lectureCategory"><xsl:value-of select="./category"/></div>
	<h1>
		<xsl:text disable-output-escaping="yes"></xsl:text><xsl:value-of select="./title" disable-output-escaping="yes"/><xsl:text disable-output-escaping="yes"></xsl:text>
	</h1>

	<xsl:if test="count(child::chair) != 0">
		<h2>
			by <xsl:apply-templates select="./chair"/>
		</h2>
	</xsl:if>

	<div class="details">
		<xsl:call-template name="prettydate">
			<xsl:with-param name="dat" select="substring(./startDate,0,11)"/>
		</xsl:call-template>
		<xsl:if test="substring(./startDate,12,5) != '00:00'">
			from <strong><xsl:value-of select="substring(./startDate,12,5)"/></strong>
		</xsl:if>
		<xsl:if test="substring(./endDate,12,5) != '00:00'">
			to <strong><xsl:value-of select="substring(./endDate,12,5)"/></strong>
		</xsl:if>
		(<xsl:value-of select="substring(./timezone,0,25)"/>)

		<xsl:if test="count(child::location) != 0 and (./location/name !='' or ./location/room !='')">
			<br />at <xsl:apply-templates select="./location"><xsl:with-param name="span">headerRoomLink</xsl:with-param></xsl:apply-templates>
		</xsl:if>
	</div>
    <xsl:call-template name="displayModifIcons">
      <xsl:with-param name="item" select="."/>
      <xsl:with-param name="confId" select="/iconf/ID"/>
      <xsl:with-param name="sessId" value=""/>
      <xsl:with-param name="sessCode" value=""/>
      <xsl:with-param name="contId" value=""/>
      <xsl:with-param name="subContId" value=""/>
      <xsl:with-param name="alignMenuRight">true</xsl:with-param>
      <xsl:with-param name="manageLink">true</xsl:with-param>
      <xsl:with-param name="manageLinkBgColor">white</xsl:with-param>
      <xsl:with-param name="uploadURL">Indico.Urls.UploadAction.conference</xsl:with-param>
    </xsl:call-template>
</xsl:template>

<xsl:template match="chair|announcer">
  <xsl:for-each select="*">
    <xsl:if test="name() = 'user'">
      <xsl:call-template select="." name="fulluser">
	<xsl:with-param name="span">author</xsl:with-param>
      </xsl:call-template>
    </xsl:if>
    <xsl:if test="name() = 'UnformatedUser'">
      <xsl:apply-templates select="." />
    </xsl:if>
    <xsl:if test="count(following-sibling::*) != 0">, </xsl:if>
  </xsl:for-each>
</xsl:template>

<xsl:template match="convener|speakers">
	<xsl:for-each select="./user|./UnformatedUser">
	<xsl:apply-templates select=".">
		<xsl:with-param name="span"></xsl:with-param>
	</xsl:apply-templates>
	<xsl:if test="count(following-sibling::user) != 0">,</xsl:if>
	</xsl:for-each>
</xsl:template>

</xsl:stylesheet>
