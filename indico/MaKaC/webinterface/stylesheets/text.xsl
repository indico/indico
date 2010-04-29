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
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns:date="http://exslt.org/dates-and-times">

<xsl:include href="include/common.xsl"/>
<xsl:output method="text" version="1.0" encoding="UTF-8" indent="no"/>

<!-- GLobal object: Agenda -->
<xsl:template match="iconf">
<xsl:value-of select="./title"/><xsl:text>  </xsl:text>(<xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template><xsl:if test="substring(./startDate,0,11) != substring(./endDate,0,11)"><xsl:text> to </xsl:text><xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./endDate,0,11)"/></xsl:call-template></xsl:if>)(<xsl:apply-templates select="./location"/>)
<xsl:if test="./description != ''"><xsl:text>
__________________________________________________________
Description: </xsl:text><xsl:value-of select="./description"/></xsl:if>

<xsl:if test="./participants != ''"><xsl:text>
__________________________________________________________
Participants: </xsl:text><xsl:value-of select="./participants"/></xsl:if>
<xsl:if test="./videoconference != ''"><xsl:text>
__________________________________________________________
Videoconference: </xsl:text><xsl:for-each select="./videoconference"><xsl:apply-templates select="."/></xsl:for-each></xsl:if>
<xsl:if test="./audioconference != ''"><xsl:text>
__________________________________________________________
Audioconference: </xsl:text><xsl:for-each select="./audioconference"><xsl:apply-templates select="."/></xsl:for-each></xsl:if>
__________________________________________________________
<xsl:for-each select="./session|./contribution|./break">
<xsl:text>

</xsl:text>
<xsl:if test="substring(./startDate,0,11) != substring(preceding-sibling::startDate,0,11)">
	<xsl:call-template name="prettydate"><xsl:with-param name="dat" select="substring(./startDate,0,11)"/></xsl:call-template>
__________________________________________________________

</xsl:if>
	<xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>

<xsl:template match="session">
<xsl:if test="./title != ''">
    <xsl:value-of select="./title"/><xsl:text>  </xsl:text> <xsl:if test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">(<xsl:apply-templates select="./location"/>)</xsl:if>
<xsl:if test="./description != ''"><xsl:text>
----------------------------------------
</xsl:text><xsl:value-of select="./description"/>
</xsl:if>
----------------------------------------
</xsl:if>
<xsl:for-each select="contribution|break">
	<xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>


<xsl:template match="break">
<xsl:text>
</xsl:text>
	<xsl:if test="substring(./startDate,12,5) != '00:00'">
	 <xsl:value-of select="substring(./startDate,12,5)"/><xsl:text>   </xsl:text>
	</xsl:if>
	<xsl:value-of select="./name"/>
<xsl:text>
</xsl:text>
</xsl:template>

<xsl:template match="contribution">
<xsl:text>
</xsl:text>
	        <xsl:if test="substring(./startDate,12,5) != '00:00'">
	                <xsl:value-of select="substring(./startDate,12,5)"/><xsl:text>   </xsl:text>
	        </xsl:if>

	<xsl:value-of select="./title"/>
    <xsl:apply-templates select="./speakers"/> <xsl:if test="(./location/name != ../location/name and ./location/name != '') or (./location/room != ../location/room and ./location/room != '' and ./location/room != '0--')">(<xsl:apply-templates select="./location"/>)</xsl:if><xsl:text>
</xsl:text>
        <xsl:if test="./abstract != ''"><xsl:value-of select="./abstract"/><xsl:text>
</xsl:text>
	</xsl:if>

<xsl:for-each select="subcontribution">
	<xsl:apply-templates select="."/>
</xsl:for-each>
</xsl:template>


<xsl:template match="subcontribution">
<xsl:text>
    o </xsl:text>
	<xsl:value-of select="./title"/>
	<xsl:apply-templates select="./speakers"/><xsl:text>
</xsl:text>
        <xsl:if test="./abstract != ''"><xsl:value-of select="./abstract"/><xsl:text>
</xsl:text>
	</xsl:if>
</xsl:template>

<xsl:template match="location">
        <xsl:param name="span"/>
        <xsl:value-of select="./name"/>
        <xsl:if test="./room != '0--' and ./room != 'Select:' and (name(..)='iconf' or ./room != ../../location/room)">(<span class="{$span}"><xsl:value-of select="./room" disable-output-escaping="yes"/></span>)</xsl:if>
</xsl:template>

<xsl:template name="prettydate">
	<xsl:param name="dat" select="0"/>
	<xsl:value-of select="date:day-name($dat)"/>
	<xsl:text disable-output-escaping="yes"> </xsl:text>
	<xsl:value-of select="substring($dat,9,2)"/>
	<xsl:text disable-output-escaping="yes"> </xsl:text>
	<xsl:value-of select="date:month-name($dat)"/>
	<xsl:text disable-output-escaping="yes"> </xsl:text>
	<xsl:value-of select="substring($dat,1,4)"/>
</xsl:template>

<xsl:template match="speakers">
    <xsl:for-each select="./user|./UnformatedUser">
        <xsl:text disable-output-escaping="yes"> (</xsl:text>
	<xsl:apply-templates select="."><xsl:with-param name="span"></xsl:with-param></xsl:apply-templates>
        <xsl:if test="count(following-sibling::user) != 0">,<xsl:text disable-output-escaping="yes"> </xsl:text></xsl:if>
        <xsl:text disable-output-escaping="yes"> )</xsl:text>
</xsl:for-each>
</xsl:template>

<xsl:template match="user">
	<xsl:param name="span" default=""/>
	<xsl:apply-templates select="./name"/>
	<xsl:if test="./organization != ''"><xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>(<i><xsl:value-of select="./organization" disable-output-escaping="yes"/></i>)</xsl:if>
</xsl:template>

<xsl:template match="name">
	<xsl:value-of select="./@first" disable-output-escaping="yes"/>
	<xsl:if test="./@first!='' and ./@last!=''">
		<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	</xsl:if>
	<xsl:value-of select="./@last" disable-output-escaping="yes"/>
</xsl:template>	

</xsl:stylesheet>
