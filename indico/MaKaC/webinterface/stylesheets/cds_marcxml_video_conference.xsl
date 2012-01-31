<?xml version='1.0'?>
<!-- $Id: cds_marcxml_presentation.xsl,v 1.2 2008/04/24 16:59:56 jose Exp $

     This file is part of Indico.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.

     Indico is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     Indico is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with Indico; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
-->

<xsl:stylesheet version='1.0' xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>

<!-- Event -->
<xsl:template match="event">

<record xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">
<datafield tag="041" ind1=" " ind2=" ">
  <xsl:choose>
    <xsl:when test="./languages != ''">
      <xsl:for-each select="./languages/code">
        <subfield code="a"><xsl:value-of select="." /></subfield>
      </xsl:for-each>
    </xsl:when>
    <xsl:otherwise>
      <subfield code="a">eng</subfield>
    </xsl:otherwise>
  </xsl:choose>
</datafield>
<datafield tag="110" ind1=" " ind2=" ">
  <subfield code="a">CERN. Geneva</subfield>
</datafield>
<datafield tag="111" ind1=" " ind2=" ">
  <xsl:if test="./title!=''">
  <subfield code="a"><xsl:value-of select="./title"/></subfield>
  </xsl:if>
  <subfield code="c"><xsl:value-of select="./location/name" disable-output-escaping="yes"/> - <xsl:value-of select="./location/room" disable-output-escaping="yes"/></subfield>
  <subfield code="9"><xsl:value-of select="./startDate" disable-output-escaping="yes"/></subfield>
  <subfield code="z"><xsl:value-of select="./endDate" disable-output-escaping="yes"/></subfield>
  <subfield code="g"><xsl:value-of select="./ID" disable-output-escaping="yes"/></subfield>
</datafield>
<xsl:if test="./title!=''">
<datafield tag="245" ind1=" " ind2=" ">
  <subfield code="a"><xsl:value-of select="./title"/></subfield>
</datafield>
</xsl:if>
<datafield tag="260" ind1=" " ind2=" ">
  <subfield code="c"><xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="269" ind1=" " ind2=" ">
  <subfield code="c"><xsl:value-of select="substring(./startDate,0,11)" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="300" ind1=" " ind2=" ">
  <subfield code="a">Streaming video</subfield>
  <subfield code="b"><xsl:value-of select="./videoFormat" /></subfield>
</datafield>
<datafield tag="340" ind1=" " ind2=" ">
  <subfield code="a">Streaming video</subfield>
</datafield>
<datafield tag="490" ind1=" " ind2=" ">
  <subfield code="a"><xsl:value-of select="./category"/></subfield>
<xsl:if test="substring(./category,0,26)='Academic Training Lecture'">
  <subfield code="v">
  <xsl:choose>
  <xsl:when test="substring(./startDate,6,2)='01' or substring(./startDate,6,2)='02' or substring(./startDate,6,2)='03' or substring(./startDate,6,2)='04' or substring(./startDate,6,2)='05' or substring(./startDate,6,2)='06' or substring(./startDate,6,2)='07' or substring(./startDate,6,2)='08'">
<xsl:value-of select="number(substring(./startDate,0,5))-1" disable-output-escaping="yes"/>-<xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/>
  </xsl:when>
  <xsl:otherwise>
<xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/>-<xsl:value-of select="number(substring(./startDate,0,5))+1" disable-output-escaping="yes"/>
  </xsl:otherwise>
  </xsl:choose>
  </subfield>
</xsl:if>
<xsl:if test="substring(./category,0,23)='Summer Student Lecture'">
  <subfield code="v"><xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/></subfield>
</xsl:if>
</datafield>
<xsl:if test="./allowedAccessGroups != '' and count(./allowedAccessGroups) != 0">
<datafield tag="506" ind1="1" ind2=" ">
    <subfield code="a">Restricted</subfield>
    <xsl:for-each select="./allowedAccessGroups/group">
    <subfield code="d"><xsl:value-of select="." /></subfield>
    </xsl:for-each>
    <subfield code="f">group</subfield>
    <subfield code="2">CDS Invenio</subfield>
    <subfield code="5">SzGeCERN</subfield>
</datafield>
</xsl:if>
<xsl:if test="./allowedAccessEmails != '' and count(./allowedAccessEmails) != 0">
<datafield tag="506" ind1="1" ind2=" ">
    <subfield code="a">Restricted</subfield>
    <xsl:for-each select="./allowedAccessEmails/email">
    <subfield code="d"><xsl:value-of select="." /></subfield>
    </xsl:for-each>
    <subfield code="f">email</subfield>
    <subfield code="2">CDS Invenio</subfield>
    <subfield code="5">SzGeCERN</subfield>
</datafield>
</xsl:if>
<datafield tag="518" ind1=" " ind2=" ">
  <subfield code="d"><xsl:value-of select="./startDate" disable-output-escaping="yes"/></subfield>
</datafield>
<xsl:if test="./description!=''">
<datafield tag="520" ind1=" " ind2=" ">
  <subfield code="a">&lt;!--HTML--&gt;<xsl:value-of select="./description"/></subfield>
</datafield>
</xsl:if>
<datafield tag="650" ind1="1" ind2="7">
  <subfield code="a"><xsl:value-of select="./category"/></subfield>
</datafield>
<datafield tag="650" ind1="2" ind2="7">
  <subfield code="a">Event</subfield>
</datafield>
<datafield tag="690" ind1="C" ind2=" ">
  <subfield code="a">TALK</subfield>
</datafield>
<datafield tag="690" ind1="C" ind2=" ">
  <subfield code="a">CERN</subfield>
</datafield>
<xsl:if test="count(./CDSExperiment) != 0">
<datafield tag="693" ind1=" " ind2=" ">
  <subfield code="e"><xsl:value-of select="./CDSExperiment" disable-output-escaping="yes"/></subfield>
</datafield>
</xsl:if>
<xsl:if test="count(./chair) != 0">
<xsl:for-each select="./chair/user">
<datafield tag="700" ind1=" " ind2=" ">
  <subfield code="a"><xsl:apply-templates select="./name"/></subfield>
  <subfield code="e">speaker</subfield>
  <xsl:if test="./organization != ''">
  <subfield code="u"><xsl:value-of select="./organization"/></subfield>
  </xsl:if>
</datafield>
</xsl:for-each>
</xsl:if>
<datafield tag="856" ind1="4" ind2=" ">
  <subfield code="u">http://indico.cern.ch/conferenceDisplay.py?confId=<xsl:value-of select="./ID" disable-output-escaping="yes"/></subfield>
  <subfield code="y">Event details</subfield>
</datafield>
<datafield tag="859" ind1=" " ind2=" ">
  <subfield code="f"><xsl:apply-templates select="./announcer/user/email"/></subfield>
</datafield>
<xsl:if test="count(./chair) != 0">
  <xsl:for-each select="./chair/user">
<datafield tag="906" ind1=" " ind2=" ">
  <subfield code="p"><xsl:apply-templates select="./name"/></subfield>
  <xsl:if test="./organization != ''">
  <subfield code="u"><xsl:value-of select="./organization"/></subfield>
  </xsl:if>
</datafield>
  </xsl:for-each>
</xsl:if>
<datafield tag="961" ind1=" " ind2=" ">
  <subfield code="x"><xsl:value-of select="./creationDate" disable-output-escaping="yes"/></subfield>
  <subfield code="c"><xsl:value-of select="./modificationDate" disable-output-escaping="yes"/></subfield>
</datafield>
<xsl:if test="substring(./category,0,26)='Academic Training Lecture'">
<datafield tag="962" ind1=" " ind2=" ">
  <subfield code="n">cern<xsl:choose>
  <xsl:when test="substring(./startDate,6,2)='01' or substring(./startDate,6,2)='02' or substring(./startDate,6,2)='03' or substring(./startDate,6,2)='04' or substring(./startDate,6,2)='05' or substring(./startDate,6,2)='06' or substring(./startDate,6,2)='07' or substring(./startDate,6,2)='08'">
<xsl:value-of select="number(substring(./startDate,0,5))-1" disable-output-escaping="yes"/>
  </xsl:when>
  <xsl:otherwise>
<xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/>
  </xsl:otherwise>
  </xsl:choose>0901</subfield>
</datafield>
</xsl:if>
<xsl:if test="substring(./category,0,23)='Summer Student Lecture'">
<datafield tag="962" ind1=" " ind2=" ">
  <subfield code="n">cern<xsl:value-of select="substring(./startDate,0,5)" disable-output-escaping="yes"/>0701</subfield>
</datafield>
</xsl:if>
<datafield tag="963" ind1=" " ind2=" ">
  <subfield code="a">PUBLIC</subfield>
</datafield>
<datafield tag="970" ind1=" " ind2=" ">
  <subfield code="a">INDICO.<xsl:value-of select="./ID" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="a">Indico</subfield>
</datafield>
<xsl:if test="count(./CDSCategories) != 0">
<datafield tag="980" ind1=" " ind2=" ">
<xsl:for-each select="./CDSCategories/category">
  <subfield code="a"><xsl:value-of select="." disable-output-escaping="yes"/></subfield>
</xsl:for-each>
</datafield>
</xsl:if>
<xsl:if test="substring(./category,0,26)='Academic Training Lecture'">
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="b">ACAD</subfield>
</datafield>
</xsl:if>
<xsl:if test="substring(./category,0,23)='Summer Student Lecture'">
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="b">SSLP</subfield>
</datafield>
</xsl:if>
<xsl:if test="substring(./category,0,23)!='Summer Student Lecture' and substring(./category,0,26)!='Academic Training Lecture'">
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="b">TALK</subfield>
</datafield>
</xsl:if>
</record>

</xsl:template>

<xsl:template match="name">
  <xsl:value-of select="./@last" disable-output-escaping="yes"/>
  <xsl:if test="./@first!='' and ./@last!=''">
  <xsl:text disable-output-escaping="yes">, </xsl:text>
  </xsl:if>
  <xsl:value-of select="./@first" disable-output-escaping="yes"/>
</xsl:template>

</xsl:stylesheet>


