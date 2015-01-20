<?xml version='1.0'?>
<!--

   This file is part of Indico.
   Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).

   Indico is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 3 of the
   License, or (at your option) any later version.

   Indico is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Indico; if not, see <http://www.gnu.org/licenses/>.
-->
<xsl:stylesheet version='1.0' xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
<!--  Generate the DOCTYPE for lecture.xml -->
<xsl:output
        method="LECTURE"
        doctype-system="http://www.wlap.org/dtd/lecture.dtd"
        indent="yes"/>

<!-- Event -->
<xsl:template match="event">

<LECTURE>
  <xsl:attribute name="TITLE"><xsl:value-of select="./contribution/subcontribution/title" /></xsl:attribute>
  <xsl:choose>
    <xsl:when test="./contribution/subcontribution/speakers/user != ''">
      <xsl:for-each select="./contribution/subcontribution/speakers/user">
        <AUTHOR><xsl:apply-templates select="./name"/></AUTHOR>
      </xsl:for-each>
    </xsl:when>
    <xsl:otherwise>
      <AUTHOR>no speaker given</AUTHOR>
    </xsl:otherwise>
  </xsl:choose>
  <DATE><xsl:value-of select="substring(./startDate, 0, 11)" /></DATE>
  <LANGUAGE>
    <xsl:choose>
      <xsl:when test="./contribution/subcontribution/languages != ''">
        <xsl:for-each select="./contribution/subcontribution/languages/code">
          <xsl:value-of select="." />
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise>
        <LANGUAGE>eng</LANGUAGE>
      </xsl:otherwise>
    </xsl:choose>
  </LANGUAGE>
  <DURATION><xsl:value-of select="./contribution/subcontribution/duration"/></DURATION>
  <TIME><xsl:value-of select="substring(./contribution/startDate, 12, 8)" disable-output-escaping="yes"/></TIME>
  <PAR>
    <VIDEO REGION="speaker-face">
    <SWITCH>
      <REF SRC="media/master.flv" TYPE="video/flash" WIDTH="240" HEIGHT="160" AUDIO="Yes" VIDEO="Yes" AVERAGERATE="" ADAPTIVE="No"/>
    </SWITCH>
    </VIDEO>
    <SEQ TITLE="Sequence of slides" REGION="slide" >
        <!-- This section will be populated by a list of slide timings later -->
    </SEQ>
  </PAR>
</LECTURE>

</xsl:template>

<xsl:template match="name">
  <xsl:value-of select="./@last" disable-output-escaping="yes"/>
  <xsl:if test="./@first!='' and ./@last!=''">
  <xsl:text disable-output-escaping="yes">, </xsl:text>
  </xsl:if>
  <xsl:value-of select="./@first" disable-output-escaping="yes"/>
</xsl:template>

</xsl:stylesheet>
