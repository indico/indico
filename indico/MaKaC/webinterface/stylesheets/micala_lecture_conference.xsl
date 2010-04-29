<?xml version='1.0'?>
<!-- This file is part of CDS Indico.
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

<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>

<!-- Event -->
<xsl:template match="event">

<!DOCTYPE LECTURE SYSTEM "http://www.wlap.org/dtd/lecture.dtd">
<LECTURE TITLE="<xsl:value-of select="./title"/>">
<xsl:for-each select="./chair/user">
<AUTHOR><xsl:apply-templates select="./name"/></AUTHOR>
</xsl:for-each>
<DATE><xsl:value-of select="./startDate" disable-output-escaping="yes"/></DATE>
<LANGUAGE>
  <xsl:choose>
    <xsl:when test="./languages != ''">
      <xsl:for-each select="./languages/code">
        <LANGUAGE><xsl:value-of select="." /></LANGUAGE>
      </xsl:for-each>
    </xsl:when>
    <xsl:otherwise>
      <LANGUAGE>eng</LANGUAGE>
    </xsl:otherwise>
  </xsl:choose>
</LANGUAGE>
<DURATION><xsl:value-of select="./duration"/></DURATION>
<TIME><xsl:value-of select="./startDate" disable-output-escaping="yes"/></TIME>
<PAR>
<VIDEO REGION="speaker-face">
<SWITCH>
<REF SRC="media/master.flv" TYPE="video/flash" WIDTH="240" HEIGHT="160" AUDIO="Yes" VIDEO="Yes" AVERAGERATE="" ADAPTIVE="No"/>
</SWITCH>
</VIDEO>
<SEQ TITLE="Sequence of slides" REGION="slide" >
</SEQ>
</PAR>
</LECTURE>