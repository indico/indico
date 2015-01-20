<?xml version='1.0'?>
<!--

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
  <subfield code="a">eng</subfield>
</datafield>
<datafield tag="110" ind1=" " ind2=" ">
  <subfield code="a">CERN. Geneva</subfield>
</datafield>
<datafield tag="111" ind1=" " ind2=" ">
  <xsl:if test="./title!=''">
  <subfield code="a"><xsl:value-of select="./title"/></subfield>
  </xsl:if>
  <subfield code="c"><xsl:value-of select="./location/name" disable-output-escaping="yes"/> - <xsl:value-of select="./location/room" disable-output-escaping="yes"/></subfield>
  <subfield code="9"><xsl:value-of select="./contribution/startDate" disable-output-escaping="yes"/></subfield>
  <subfield code="z"><xsl:value-of select="./contribution/endDate" disable-output-escaping="yes"/></subfield>
  <subfield code="g"><xsl:value-of select="./ID" disable-output-escaping="yes"/></subfield>
</datafield>
<xsl:if test="./contribution/title!=''">
<datafield tag="245" ind1=" " ind2=" ">
  <subfield code="a"><xsl:value-of select="./contribution/title"/></subfield>
</datafield>
</xsl:if>
<datafield tag="260" ind1=" " ind2=" ">
  <subfield code="c"><xsl:value-of select="substring(./contribution/startDate,0,5)" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="269" ind1=" " ind2=" ">
  <subfield code="c"><xsl:value-of select="substring(./contribution/startDate,0,11)" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="300" ind1=" " ind2=" ">
  <subfield code="a">Streaming video</subfield>
  <subfield code="b">720x576 4/3, 25</subfield>
</datafield>
<datafield tag="340" ind1=" " ind2=" ">
  <subfield code="a">Streaming video</subfield>
</datafield>
<datafield tag="490" ind1=" " ind2=" ">
  <subfield code="a"><xsl:value-of select="./category"/></subfield>
</datafield>
<datafield tag="490" ind1=" " ind2=" ">
  <subfield code="a"><xsl:value-of select="./title" /></subfield>
</datafield>
<datafield tag="518" ind1=" " ind2=" ">
  <subfield code="d"><xsl:value-of select="./contribution/startDate" disable-output-escaping="yes"/></subfield>
</datafield>
<xsl:if test="./contribution/abstract!=''">
<datafield tag="520" ind1=" " ind2=" ">
  <subfield code="a">&lt;!--HTML--&gt;<xsl:value-of select="./contribution/abstract"/></subfield>
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
<xsl:if test="count(./contribution/speakers) != 0">
<xsl:for-each select="./contribution/speakers/user">
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
  <subfield code="u">http://indico.cern.ch/contributionDisplay.py?confId=<xsl:value-of select="./ID" disable-output-escaping="yes"/>&amp;contribId=<xsl:value-of select="./contribution/ID" disable-output-escaping="yes"/></subfield>
  <subfield code="y">Talk details</subfield>
</datafield>
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
<datafield tag="963" ind1=" " ind2=" ">
  <subfield code="a">PUBLIC</subfield>
</datafield>
<datafield tag="970" ind1=" " ind2=" ">
  <subfield code="a">INDICO.<xsl:value-of select="./ID" disable-output-escaping="yes"/>c<xsl:value-of select="./contribution/ID" disable-output-escaping="yes"/></subfield>
</datafield>
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="a">Indico</subfield>
</datafield>
<datafield tag="980" ind1=" " ind2=" ">
  <subfield code="b">TALK</subfield>
</datafield>

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


