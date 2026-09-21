import os

from xml2db import DataModel
from xml2db.xml_converter import XMLConverter
from .conftest import models_path

xsd_path = os.path.join(models_path, "imported_namespaces", "main.xsd")
xml_path = os.path.join(models_path, "imported_namespaces", "xml", "basket1.xml")


def build_model():
    return DataModel(str(xsd_path), short_name="imported_namespaces")


def iter_nodes(node):
    """Yield all nodes of a document tree recursively"""
    yield node
    for values in node[1].values():
        for value in values:
            if isinstance(value, tuple):
                yield from iter_nodes(value)


def test_imported_namespace_types_are_not_merged():
    """Types sharing a local name across namespaces are mapped to distinct tables"""

    model = build_model()

    assert sorted(model.tables.keys()) == ["basketType", "itemType", "itemType_1"]
    assert sorted(model.names_types_map.keys()) == ["basket", "item", "item_1"]
    assert sorted(model.tables["itemType"].columns.keys()) == ["label"]
    assert sorted(model.tables["itemType_1"].columns.keys()) == ["code", "quantity"]


def test_imported_namespace_fields_are_parsed():
    """Content defined in the imported schema is parsed into its own nodes"""

    model = build_model()
    converter = XMLConverter(model)

    parsed_recursive = converter.parse_xml(xml_path, skip_validation=False)
    parsed_iterative = converter.parse_xml(
        xml_path, skip_validation=False, iterparse=True
    )

    assert parsed_recursive == parsed_iterative

    imported_nodes = [
        node for node in iter_nodes(parsed_recursive) if node[0] == "itemType_1"
    ]
    assert [node[1]["code"][0] for node in imported_nodes] == ["APL", "APL-2", "ORG"]
    assert [node[1]["quantity"][0] for node in imported_nodes] == [3, 5, 7]
