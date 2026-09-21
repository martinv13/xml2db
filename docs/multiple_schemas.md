---
title: "Combining several XSD schemas"
description: "How to load XML documents which mix several XML schemas with xml2db, by writing a wrapper XSD which imports them and replaces xs:any wildcards."
---

# Combining several XSD schemas

`xml2db` builds a data model from a single XSD file, but that file can pull in as many other schemas as needed with
`xs:import` (for another namespace) and `xs:include` (for the same namespace). Documents mixing several namespaces are
therefore supported, provided that a single schema describes the whole document.

Two situations require a bit of work:

* the container schema declares its payload as a wildcard (`xs:any`), so it does not say which elements may appear,
* the schemas are complete, but no single file references all of them.

Both are solved by writing a small wrapper schema of your own, which imports the other schemas and declares the
payload explicitly.

## Replacing a wildcard with the payload schema

`xml2db` ignores `xs:any` children and logs a warning, because a wildcard gives no structure to map to tables. This
is common in container formats: protocol envelopes such as SOAP or SRU carry an arbitrary payload, which its own
schema describes.

The example below covers the [SRU](https://www.loc.gov/standards/sru/) API of the French national library, which
returns [MarcXchange](https://www.loc.gov/standards/iso25577/) records inside an SRU envelope. The SRU schema declares
`recordData` as a wildcard, so the wrapper declares it as holding a `record` element from the MarcXchange namespace:

``` xml title="sru-marcxchange.xsd" linenums="1"
<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:srw="http://www.loc.gov/zing/srw/"
           xmlns:mxc="info:lc/xmlns/marcxchange-v2"
           targetNamespace="http://www.loc.gov/zing/srw/"
           elementFormDefault="qualified">

    <xs:import namespace="info:lc/xmlns/marcxchange-v2"
               schemaLocation="marcxchange-2-0.xsd"/>

    <xs:element name="searchRetrieveResponse" type="srw:responseType"/>

    <xs:complexType name="responseType">
        <xs:all>
            <xs:element name="version" type="xs:string"/>
            <xs:element name="numberOfRecords" type="xs:integer"/>
            <xs:element name="records" type="srw:recordsType" minOccurs="0"/>
            <xs:element name="nextRecordPosition" type="xs:integer" minOccurs="0"/>
        </xs:all>
    </xs:complexType>

    <xs:complexType name="recordsType">
        <xs:sequence>
            <xs:element name="record" type="srw:srwRecordType" minOccurs="0" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>

    <xs:complexType name="srwRecordType">
        <xs:sequence>
            <xs:element name="recordSchema" type="xs:string"/>
            <xs:element name="recordPacking" type="xs:string" minOccurs="0"/>
            <xs:element name="recordData" type="srw:recordDataType"/>
            <xs:element name="recordIdentifier" type="xs:string" minOccurs="0"/>
            <xs:element name="recordPosition" type="xs:integer" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>

    <!-- The SRU schema declares recordData as a wildcard. Here it is declared as
         holding a MarcXchange record, which xml2db can map to tables. -->
    <xs:complexType name="recordDataType">
        <xs:sequence>
            <xs:element ref="mxc:record"/>
        </xs:sequence>
    </xs:complexType>

</xs:schema>
```

Save `marcxchange-2-0.xsd` next to the wrapper, or point `schemaLocation` to its URL, and load documents as usual:

``` py linenums="1"
from xml2db import DataModel

model = DataModel(
    xsd_file="sru-marcxchange.xsd",
    short_name="sru_marcxchange",
    connection_string="duckdb:///sru.duckdb",
)
model.create_db_schema()
model.create_all_tables()

document = model.parse_xml("search_retrieve_response.xml")
document.insert_into_target_tables()
```

The MarcXchange records are then queryable, joining the `record` table with the `datafield` and `subfield` tables
derived from the imported schema.

## Writing the wrapper

A few points worth checking when writing a wrapper schema:

* **Element order**: `xs:sequence` requires the exact order declared in the schema. Servers do not always follow the
  order of the reference schema, `xs:all` accepts any order for elements occurring at most once.
* **Undeclared elements**: elements missing from the wrapper are parsed and ignored, so a partial wrapper covering only
  the elements you need is fine.
* **Type names**: `xml2db` identifies complex types by their local name, ignoring their namespace. Two types named
  `recordType` in two namespaces get the keys `recordType` and `recordType_1`, with a warning. Table names are derived
  from element names and remain unaffected, but naming types explicitly in your own schema, as `srwRecordType` above,
  keeps the model easier to read and to configure.
* **Validation**: `parse_xml` does not validate documents unless `skip_validation=False` is passed. Payloads often
  deviate from their reference schema on details such as patterns or `xs:ID` attributes. If validation matters, relax
  the corresponding facets in your local copy of the schema.
* **Recursive types**: fields introducing a cycle are discarded with a warning, as described in
  [Caveats](how_it_works.md#recursive-xsd). The MarcXchange `embeddeddata` element is one of them, so embedded records
  are not imported.
