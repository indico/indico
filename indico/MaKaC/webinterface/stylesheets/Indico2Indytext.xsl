<?xml version="1.0" encoding="utf-8"?>
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
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="text" version="1.0" encoding="utf-8" indent="yes"/>

<!--
Darudh Birker CERN, DSU-CO   August 2007-Stylesheet to transform the CERN Indico XML file
to a tagged text Adobe Indesign file.
-->

<xsl:template match="/">

<formatted-iconf>

<xsl:apply-templates/>

</formatted-iconf>

</xsl:template>

<xsl:template match="category">
<xsl:text>&lt;ASCII-MAC&gt;&#13;</xsl:text>
<xsl:text>&lt;Version:4&gt;&lt;FeatureSet:InDesign-Roman&gt;&lt;ColorTable:=&lt;Black:COLOR:CMYK:Process:0,0,0,1&gt;&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:timestart&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:timeend&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:title&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:sessiontitle&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:convener&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:convenername&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:speakers&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:name&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:duration&gt;&#13;</xsl:text>
<xsl:text>&lt;DefineCharStyle:organization&gt;&#13;</xsl:text>
</xsl:template>

   <xsl:template match="session | break">

<xsl:if test="self::session">

&#60;CharStyle:timestart&#62;<xsl:value-of select="substring(./startDate,12,5)"/>&lt;CharStyle:&gt;
&#9;&lt;CharStyle:timeend&gt;<xsl:value-of select="substring(./endDate,12,5)"/>&lt;CharStyle:&gt;&#9;
<!--
&lt;CharStyle:duration&gt;<xsl:value-of select="./duration"/>&lt;CharStyle:&gt;&#9;
-->
&lt;CharStyle:sessiontitle&gt;<xsl:value-of select="./title"/>&lt;CharStyle:&gt;&#9;
&lt;CharStyle:convener&gt;Convener: &lt;CharStyle:&gt;&#9;
&lt;CharStyle:convenername&gt;<xsl:apply-templates select="./convener/user"/>&lt;CharStyle:&gt;&#9;

<xsl:apply-templates select="contribution"/>

</xsl:if>

<xsl:if test="self::break">
&lt;CharStyle:duration&gt;<xsl:value-of select="./duration"/>&lt;CharStyle:&gt;&#9;
<xsl:value-of select="./name"/>
<xsl:value-of select="./description"/>
</xsl:if>


   </xsl:template>



   <xsl:template match="contribution">

&lt;CharStyle:timestart&gt;<xsl:value-of select="substring(./startDate,12,5)"/>&lt;CharStyle:&gt;&#9;
&#9;&lt;CharStyle:timeend&gt;<xsl:value-of select="substring(./endDate,12,5)"/>&lt;CharStyle:&gt;&#9;
&lt;CharStyle:duration&gt;<xsl:value-of select="./duration"/>&lt;CharStyle:&gt;&#9;
&lt;CharStyle:title&gt;&#9;<xsl:value-of select="./title"/>&lt;CharStyle:&gt;&#9;
   &lt;CharStyle:speakers&gt;<xsl:apply-templates select="./speakers/user"/>&lt;CharStyle:&gt;

   </xsl:template>

   <xsl:template match="user">

   <xsl:apply-templates select="./name"/>
   <xsl:if test="./organization != ''">
   &lt;CharStyle:organization&gt;<xsl:value-of select="./organization"/>
   </xsl:if>

   </xsl:template>

   <xsl:template match="name">

   <xsl:value-of select="./@first"/>
   <xsl:if test="./@first!='' and ./@last!=''">
   <xsl:text disable-output-escaping="yes">&#32;</xsl:text>
   </xsl:if>
   <xsl:value-of select="./@last"/>&lt;CharStyle:&gt;

   </xsl:template>

</xsl:stylesheet>
