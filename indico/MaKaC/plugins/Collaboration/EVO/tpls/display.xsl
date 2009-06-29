<?xml version='1.0'?>
<!-- $Id: display.xsl,v 1.1 2009/04/25 13:56:04 dmartinc Exp $

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

<xsl:template name="EVOPluginDisplay" match="EVOPlugin">
  <tr>
    <td>
      EVO:
      <xsl:choose>
        <xsl:when test="./ongoing != '' and ./scheduled != ''">
          There is an ongoing EVO meeting and
          <xsl:if test="count(./scheduled/booking) = 1">
            1 scheduled EVO meeting.
          </xsl:if>
          <xsl:if test="count(./scheduled/booking) > 1">
            <xsl:value-of select="count(./scheduled/booking)"/>
            scheduled EVO meetings.
          </xsl:if>
        </xsl:when>
        <xsl:when test="./ongoing != ''">
          There is an ongoing EVO meeting.
        </xsl:when>
        <xsl:when test="./scheduled != ''">
          <xsl:if test="count(./scheduled/booking) = 1">
            There is 1 scheduled EVO meeting.
          </xsl:if>
          <xsl:if test="count(./scheduled/booking) > 1">
            There are
            <xsl:value-of select="count(./scheduled/booking)"/>
            scheduled EVO meetings.
          </xsl:if>
        </xsl:when>
      </xsl:choose>
    </td>
  </tr>
</xsl:template>

</xsl:stylesheet>