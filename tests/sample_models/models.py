import os.path
import sqlalchemy
import hashlib


def make_sample_index(table_name):
    def wrapped():
        yield sqlalchemy.Index(
            f"{table_name}_fk_parent_REMITTable1_idx",
            "fk_parent_REMITTable1"
        )
    return wrapped


models = [
    {
        "id": "orders",
        "long_name": "A simple model for shipment orders",
        "description": "This model was made up to be a simple case which could represent real business cases.",
        "xsd_path": "tests/sample_models/orders/orders.xsd",
        "xml_path": "tests/sample_models/orders/xml",
        "versions": [
            {
                "config": {
                    "tables": {
                        "shiporder": {"fields": {"orderperson": {"transform": False}}}
                    },
                    "record_hash_column_name": "record_hash",
                    "metadata_columns": [
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        }
                    ],
                }
            },
            {
                "config": {
                    "row_numbers": True,
                    "tables": {
                        "item": {"reuse": False},
                        "shiporder": {"fields": {"orderperson": {"transform": False}}},
                        "companyId": {"choice_transform": False},
                    },
                    "record_hash_column_name": "record_hash",
                    "record_hash_constructor": hashlib.md5,
                    "record_hash_size": 16,
                    "metadata_columns": [
                        {
                            "name": "xml2db_processed_at",
                            "type": sqlalchemy.DateTime(timezone=True),
                            "nullable": True,
                        },
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        },
                    ],
                },
            },
            {
                "config": {
                    "tables": {
                        "shiporder": {"reuse": False},
                        "item": {"fields": {"product": {"transform": False}}},
                    },
                    "metadata_columns": [
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        }
                    ],
                }
            },
        ],
    },
    {
        "id": "table1",
        "long_name": "Data model for reporting standard contracts in the European energy markets",
        "description": "This model is one of the official models published by the Agency for the cooperation of energy"
        "regulators to report energy markets transaction data.",
        "xsd_path": "tests/sample_models/table1/Table1_V2.xsd",
        "xml_path": "tests/sample_models/table1/xml",
        "versions": [
            {
                "config": {
                    "metadata_columns": [
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        }
                    ],
                }
            },
            {
                "config": {
                    "row_numbers": True,
                    "tables": {
                        "REMITTable1": {
                            "fields": {
                                "contractList": {"transform": "elevate_wo_prefix"}
                            }
                        },
                        "TradeReport": {
                            "reuse": False,
                            "as_columnstore": True,
                            "extra_args": make_sample_index("TradeReport"),
                        },
                        "OrderReport": {
                            "reuse": False,
                            "as_columnstore": True,
                            "extra_args": make_sample_index("OrderReport"),
                        },
                        "legContract": {"reuse": False},
                        "legContractId": {"reuse": False},
                    },
                    "metadata_columns": [
                        {
                            "name": "xml2db_processed_at",
                            "type": sqlalchemy.DateTime(timezone=True),
                            "nullable": True,
                        },
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        },
                    ],
                }
            },
        ],
    },
    {
        "id": "junit10",
        "long_name": "Xunit test result format generated by Pytest",
        "description": (
            "Xunit XSD was taken from https://github.com/jenkinsci/xunit-plugin/blob/master/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd"
            " and amended to remove its recursive nature."
        ),
        "xsd_path": "tests/sample_models/junit10/junit-10.xsd",
        "xml_path": "tests/sample_models/junit10/xml",
        "versions": [
            {
                "config": {
                    "metadata_columns": [
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        }
                    ],
                }
            },
            {
                "config": {
                    "tables": {
                        "junit10": {
                            "fields": {
                                "testsuites": {
                                    "transform": False,
                                }
                            }
                        }
                    },
                    "metadata_columns": [
                        {
                            "name": "input_file_path",
                            "type": sqlalchemy.String(256),
                        }
                    ],
                }
            },
        ],
    },
]


def _generate_models_output():
    """
    This function is used to generate data models representations that will be used in the tests, in order to make sure
    that no change to the resulting data model go unnoticed.
    When changes affect the model representation or SQL DDL, these outputs need to be updated and committed to the repo.
    """
    from sqlalchemy.dialects import postgresql, mssql, mysql
    from xml2db import DataModel

    for model_config in models:
        for i in range(len(model_config["versions"])):
            xsd_path = os.path.join("../../", model_config["xsd_path"])
            for dialect in [d.dialect() for d in [postgresql, mssql, mysql]]:
                model = DataModel(
                    xsd_path,
                    model_config=model_config["versions"][i]["config"],
                    short_name=model_config["id"],
                    long_name=model_config["long_name"],
                    db_type=dialect.name,
                )
                with open(
                    os.path.join(
                        os.path.dirname(xsd_path),
                        f"{model_config['id']}_ddl_{dialect.name}_version{i}.sql",
                    ),
                    "wt",
                ) as f:
                    for s in model.get_all_create_table_statements():
                        f.write(str(s.compile(dialect=dialect)))
                    for s in model.get_all_create_index_statements():
                        f.write(str(s.compile(dialect=dialect)))
                        f.write("\n\n")
            with open(
                os.path.join(
                    os.path.dirname(xsd_path),
                    f"{model_config['id']}_erd_version{i}.md",
                ),
                "wt",
            ) as f:
                f.write("```mermaid\n")
                f.write(model.get_entity_rel_diagram(text_context=False))
                f.write("\n```")


if __name__ == "__main__":
    _generate_models_output()

