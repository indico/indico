<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="yes"/> 

  <xsl:template match="/">
    <xsl:apply-templates select="marc:collection"/>
  </xsl:template>

  <xsl:template match="marc:collection">
    <records>
      <xsl:apply-templates select="marc:record"/>
    </records>
  </xsl:template>

  <xsl:template match="marc:record">
    <record>
      <xsl:if test="count(marc:datafield[@tag=611]) > 0">
	<type category="contribution" />
      </xsl:if>
      <xsl:if test="count(marc:datafield[@tag=611]) = 0">
	<type category="event" />
      </xsl:if>

      <xsl:apply-templates select="marc:datafield[@tag!=611 and @tag!=962]" />
      <parent>
	<xsl:for-each select="marc:datafield[@tag=611]">
	  <xsl:for-each select="marc:subfield[@code='a']">	  
	    <title>
	      <xsl:value-of select="text()"/>
	    </title>
	  </xsl:for-each>
	</xsl:for-each>
	<xsl:for-each select="marc:datafield[@tag=962]">
	  <xsl:for-each select="marc:subfield[@code='b']">	  
	    <code>
	      <xsl:value-of select="text()"/>
	    </code>
	  </xsl:for-each>
	</xsl:for-each>
      </parent>
    </record>
  </xsl:template>

  <xsl:template match="marc:datafield[@tag!=611]">
    <xsl:if test="@tag=035">
      <xsl:for-each select="marc:subfield[@code='a']">
	<identifier>
	  <xsl:value-of select="text()"/>
	</identifier>
      </xsl:for-each>
    </xsl:if>

    <xsl:if test="@tag=970">
      <xsl:for-each select="marc:subfield[@code='a']">
	<identifier>
	  <xsl:value-of select="text()"/>
	</identifier>
      </xsl:for-each>
    </xsl:if>

    <xsl:if test="@tag=245">	
      <xsl:for-each select="marc:subfield[@code='a']">
	<title>
	  <xsl:value-of select="text()"/>
	</title>
      </xsl:for-each>
    </xsl:if>

    <xsl:if test="@tag=518">
      <xsl:for-each select="marc:subfield[@code='r']">
	<location>
	  <xsl:value-of select="text()"/>
	</location>
      </xsl:for-each>
      <xsl:for-each select="marc:subfield[@code='d']">
	<startDate>
	  <xsl:value-of select="text()"/>
	</startDate>
      </xsl:for-each>
    </xsl:if>

    <xsl:if test="@tag=856">
      <material>
	<xsl:for-each select="marc:subfield[@code='u']">
	  <url>
	    <xsl:value-of select="text()"/>
	  </url>	
	</xsl:for-each>
	<xsl:for-each select="marc:subfield[@code='y']">
	  <description>
	    <xsl:value-of select="text()"/>
	  </description>	
	</xsl:for-each>
      </material>
    </xsl:if>

    <xsl:if test="@tag=700">
      <author>
	<xsl:for-each select="marc:subfield[@code='a']">
	  <name>
	    <xsl:value-of select="text()"/>
	  </name>	
	</xsl:for-each>
	<xsl:for-each select="marc:subfield[@code='e']">
	  <role>
	    <xsl:value-of select="text()"/>
	  </role>	
	</xsl:for-each>
	<xsl:for-each select="marc:subfield[@code='u']">
	  <affiliation>
	    <xsl:value-of select="text()"/>
	  </affiliation>
	</xsl:for-each>
      </author>
    </xsl:if>

    <xsl:if test="@tag=520">
      <xsl:for-each select="marc:subfield[@code='a']">	  
	<description>
	  <xsl:value-of select="text()"/>
	</description>
      </xsl:for-each>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>

