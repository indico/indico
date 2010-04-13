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

<xsl:template name="shortDate">
    <xsl:param name="dat" select="0"/>
    <xsl:value-of select="substring(date:day-name($dat), 1, 3)"/>
    <xsl:text disable-output-escaping="yes"> </xsl:text>
    <xsl:value-of select="substring($dat,9,2)"/>
    <xsl:text disable-output-escaping="yes">/</xsl:text>
    <xsl:value-of select="substring($dat,6,2)"/>
</xsl:template>


<xsl:template name="prettyduration">
	<xsl:param name="duration" select="0"/>
	<xsl:if test="number(substring($duration,1,2)) != '00'">
		<xsl:value-of select="translate(substring($duration,1,2),'0','')"/>h</xsl:if><xsl:value-of select="substring($duration,4,2)"/>'</xsl:template>


</xsl:stylesheet>