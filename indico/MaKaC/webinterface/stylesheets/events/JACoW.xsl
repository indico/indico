<?xml version='1.0' encoding="UTF-8"?>
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

<xsl:stylesheet version='1.0' xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:date="http://exslt.org/dates-and-times">

<!-- GLobal object: Agenda -->
<xsl:template match="iconf" xml:space="preserve">
<conference xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://bel.gsi.de/docs/xml/conference_indico.xsd" name="{./title}, {./location/name}">
<xsl:if test="count(./contribution) != 0">  <session>
    <name abbr="PLEN0">Talks outside any sessions</name>
    <xsl:call-template name="jacowdate"><xsl:with-param name="sdat" select="./startDate"/><xsl:with-param name="edat" select="./endDate"/></xsl:call-template><xsl:apply-templates select="./convener"/><xsl:apply-templates select="./contribution"/>
  </session>
</xsl:if><xsl:apply-templates select="./session"/>
</conference>
</xsl:template>

<xsl:template match="session" xml:space="preserve">
  <session>
    <name abbr="{./code}"><xsl:value-of select="./title"/></name>
    <xsl:call-template name="jacowdate"><xsl:with-param name="sdat" select="./startDate"/><xsl:with-param name="edat" select="./endDate"/></xsl:call-template><xsl:apply-templates select="./convener"/><xsl:apply-templates select="./contribution"/>
  </session>
</xsl:template>

<xsl:template match="contribution" xml:space="preserve">
    <paper>
      <abstract_id><xsl:value-of select="./ID"/></abstract_id>
      <code><xsl:value-of select="./ID"/></code>
      <pages></pages>
      <toc></toc>
      <main_class><xsl:value-of select="./track"/></main_class>
      <sub_class></sub_class>
      <publishable></publishable>
      <presentation type="{./type/id}"><xsl:value-of select="./type/name"/></presentation>
      <start_time><xsl:value-of select="translate(substring(./startDate,12,5),':','')"/></start_time>
      <duration><xsl:call-template name="prettyduration"><xsl:with-param name="duration" select="./duration"/></xsl:call-template></duration>
      <dot></dot>
      <title><xsl:value-of select="./title"/></title>
      <abstract><xsl:value-of select="./abstract"/></abstract>
      <agency></agency>
      <contributors><xsl:apply-templates select="./speakers|./coAuthors|./primaryAuthors"/>      </contributors>
      <files>
      <xsl:apply-templates select="./material"/>
      </files>
    </paper></xsl:template>

<xsl:template match="material">
    <xsl:apply-templates select="./files"/>
</xsl:template>

<xsl:template match="files">
    <xsl:apply-templates select="./file"/>
</xsl:template>

<xsl:template match="file" xml:space="preserve">
    <file>
      <platform abbrev="PC">Intel PC</platform>
      <file_type abbrev="{./type}"><xsl:value-of select="./type"/></file_type>
      <name><xsl:value-of select="./name"/></name>
      <fileURL type="{./type}"><xsl:value-of select="./url"/></fileURL>
    </file></xsl:template>

<xsl:template name="jacowdate"><xsl:param name="sdat" select="0"/><xsl:param name="edat" select="0"/>
  <date btime="{substring($sdat,12,5)}" etime="{substring($edat,12,5)}"><xsl:value-of select="substring($sdat,9,2)"/>-<xsl:value-of select="date:month-abbreviation(substring($sdat,0,11))"/>-<xsl:value-of select="substring($sdat,1,4)"/></date>
</xsl:template>

<xsl:template match="convener" xml:space="preserve">
  <chairs><xsl:for-each select="./user|./UnformatedUser">
    <chair><xsl:apply-templates select="."/>    </chair></xsl:for-each>
  </chairs>
</xsl:template>

<xsl:template match="speakers" xml:space="preserve"><xsl:for-each select="./user|./UnformatedUser">
        <contributor type="Speaker"><xsl:apply-templates select="."/>        </contributor></xsl:for-each>
</xsl:template>

<xsl:template match="coAuthors" xml:space="preserve"><xsl:for-each select="./user|./UnformatedUser">
        <contributor type="Co-Author"><xsl:apply-templates select="."/>        </contributor></xsl:for-each>
</xsl:template>

<xsl:template match="primaryAuthors" xml:space="preserve"><xsl:for-each select="./user|./UnformatedUser">
        <contributor type="Primary Author"><xsl:apply-templates select="."/>        </contributor></xsl:for-each>
</xsl:template>

<xsl:template match="UnformatedUser" xml:space="preserve">
      <lname><xsl:value-of select="." disable-output-escaping="yes"/></lname>
</xsl:template>

<xsl:template match="user" xml:space="preserve"><xsl:apply-templates select="./name"/>
        <institutions><xsl:apply-templates select="./organization"/>        </institutions>
        <emails>
        <xsl:apply-templates select="./email"/>
        </emails>
</xsl:template>

<xsl:template match="name" xml:space="preserve">
        <lname><xsl:value-of select="./@last" disable-output-escaping="yes"/></lname>
        <fname><xsl:value-of select="./@first" disable-output-escaping="yes"/></fname>
        <mname><xsl:value-of select="./@middle" disable-output-escaping="yes"/></mname></xsl:template>

<xsl:template match="organization" xml:space="preserve">
        <institute>
          <full_name abbrev="" type=""><xsl:value-of select="."/></full_name>
          <name1></name1>
          <department></department>
          <URL></URL>
          <town></town>
          <postal_code></postal_code>
          <zip_code></zip_code>
          <country_code abbrev=""></country_code>
        </institute>
</xsl:template>

<xsl:template match="email">
        <email><xsl:value-of select="."/></email>
</xsl:template>

<xsl:template name="prettyduration">
	<xsl:param name="duration" select="0"/>
	<xsl:if test="number(substring($duration,1,2)) != '00'">
		<xsl:value-of select="translate(substring($duration,1,2),'0','')"/>h</xsl:if><xsl:value-of select="substring($duration,4,2)"/></xsl:template>

</xsl:stylesheet>
