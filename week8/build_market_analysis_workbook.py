"""Build the local Week 8 Tableau Market Analysis workbook.

The generated TWBX embeds the confidential row-level market event CSV, so it
is written below outputs/week8 and remains excluded from Git.
"""

from __future__ import annotations

import argparse
import csv
import uuid
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_DIR / "outputs" / "week8" / "tableau_market_events.csv"
DEFAULT_OUTPUT = PROJECT_DIR / "outputs" / "week8" / "market_analysis.twbx"

DATASOURCE = "federated.week8marketanalysis"
CONNECTION = "hyper.week8marketevents"
HYPER_TABLE = "market_analysis.hyper"
HYPER_DIRECTORY = "Data/market_analysis"
OBJECT_ID = "tableau_market_events_csv"

COLUMNS = [
    ("EventId", "string"),
    ("EventType", "string"),
    ("EventDate", "date"),
    ("Year", "integer"),
    ("Month", "integer"),
    ("YrMo", "string"),
    ("ListingKey", "string"),
    ("PropertyType", "string"),
    ("PropertySubType", "string"),
    ("City", "string"),
    ("CountyOrParish", "string"),
    ("PostalCode", "string"),
    ("MLSAreaMajor", "string"),
    ("StateOrProvince", "string"),
    ("ListPrice", "real"),
    ("OriginalListPrice", "real"),
    ("ClosePrice", "real"),
    ("LivingArea", "real"),
    ("DaysOnMarket", "integer"),
    ("CloseToOriginalListRatio", "real"),
    ("CloseToOriginalListRatioOutlierFlag", "boolean"),
    ("CloseToOriginalListRatioEligible", "boolean"),
    ("PricePerSqFt", "real"),
    ("rate_30yr_fixed", "real"),
    ("NewListings", "integer"),
    ("ClosedSales", "integer"),
    ("RecordCount", "integer"),
    ("SourceDataset", "string"),
]

FILTER_FIELDS = ["City", "CountyOrParish", "PostalCode", "PropertySubType"]

SHEETS = [
    {
        "name": "Monthly Median Close Price",
        "measure": "ClosePrice",
        "derivation": "Median",
        "instance": "median:ClosePrice:qk",
        "format": 'c"$"#,##0;("$"#,##0)',
        "closed_only": True,
        "color": "#4e79a7",
    },
    {
        "name": "Average Days on Market",
        "measure": "DaysOnMarket",
        "derivation": "Avg",
        "instance": "avg:DaysOnMarket:qk",
        "format": "n#,##0.0",
        "closed_only": True,
        "color": "#f28e2b",
    },
    {
        "name": "Average Close-to-Original-List Ratio",
        "measure": "CloseToOriginalListRatio",
        "derivation": "Avg",
        "instance": "avg:CloseToOriginalListRatio:qk",
        "format": "p0.0%",
        "closed_only": True,
        "color": "#59a14f",
    },
    {
        "name": "New Listings",
        "measure": "NewListings",
        "derivation": "Sum",
        "instance": "sum:NewListings:qk",
        "format": "n#,##0",
        "closed_only": False,
        "color": "#e15759",
    },
    {
        "name": "Closed Sales",
        "measure": "ClosedSales",
        "derivation": "Sum",
        "instance": "sum:ClosedSales:qk",
        "format": "n#,##0",
        "closed_only": False,
        "color": "#76b7b2",
    },
]


def xml_escape(value: str) -> str:
    """Escape a value for use in XML text and attributes."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def new_uuid() -> str:
    return "{" + str(uuid.uuid4()).upper() + "}"


def metadata_records() -> str:
    remote_types = {
        "string": "129",
        "date": "133",
        "integer": "20",
        "real": "5",
        "boolean": "16",
    }
    rows = ["        <metadata-records>"]
    for ordinal, (name, datatype) in enumerate(COLUMNS):
        aggregation = "Year" if datatype == "date" else (
            "Count" if datatype in {"string", "boolean"} else "Sum"
        )
        rows.extend(
            [
                "          <metadata-record class='column'>",
                f"            <remote-name>{xml_escape(name)}</remote-name>",
                f"            <remote-type>{remote_types[datatype]}</remote-type>",
                f"            <local-name>[{xml_escape(name)}]</local-name>",
                "            <parent-name>[Extract]</parent-name>",
                f"            <remote-alias>{xml_escape(name)}</remote-alias>",
                f"            <ordinal>{ordinal}</ordinal>",
                f"            <local-type>{datatype}</local-type>",
                f"            <aggregation>{aggregation}</aggregation>",
                "            <contains-null>true</contains-null>",
                f"            <object-id>[{OBJECT_ID}]</object-id>",
                "          </metadata-record>",
            ]
        )
    rows.append("        </metadata-records>")
    return "\n".join(rows)


def datasource_xml() -> str:
    top_columns = []
    for name, datatype in COLUMNS:
        role = "dimension" if datatype in {"string", "date", "boolean"} else "measure"
        field_type = "ordinal" if datatype == "date" else (
            "nominal" if datatype in {"string", "boolean"} else "quantitative"
        )
        semantic = ""
        if name == "City":
            semantic = " semantic-role='[City].[Name]'"
        elif name == "CountyOrParish":
            semantic = " semantic-role='[County].[Name]'"
        elif name == "PostalCode":
            semantic = " semantic-role='[ZipCode].[Name]'"
        default_format = ""
        if name in {"ListPrice", "OriginalListPrice", "ClosePrice"}:
            default_format = " default-format='c&quot;$&quot;#,##0;(&quot;$&quot;#,##0)'"
        elif name == "CloseToOriginalListRatio":
            default_format = " default-format='p0.0%'"
        top_columns.append(
            f"      <column datatype='{datatype}'{default_format} name='[{xml_escape(name)}]' "
            f"role='{role}'{semantic} type='{field_type}' />"
        )
    return f"""    <datasource caption='Week 8 Market Events' inline='true' name='{DATASOURCE}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='Week 8 Market Events' name='{CONNECTION}'>
            <connection authentication='auth-none' author-locale='en_US' class='hyper' dbname='{HYPER_DIRECTORY}/{HYPER_TABLE}' default-settings='yes' port='' sslmode='' username='tableau_internal_user' />
          </named-connection>
        </named-connections>
        <relation connection='{CONNECTION}' name='Extract' table='[Extract].[Extract]' type='table' />
{metadata_records()}
      </connection>
      <aliases enabled='yes' />
{chr(10).join(top_columns)}
      <column caption='Week 8 Market Events' datatype='table' name='[__tableau_internal_object_id__].[{OBJECT_ID}]' role='measure' type='quantitative' />
      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;United States&quot;' />
      </semantic-values>
      <object-graph>
        <objects>
          <object caption='Week 8 Market Events' id='{OBJECT_ID}'>
            <properties context=''>
              <relation connection='{CONNECTION}' name='Extract' table='[Extract].[Extract]' type='table' />
            </properties>
          </object>
        </objects>
      </object-graph>
    </datasource>"""


def dependency_column(name: str) -> str:
    datatype = dict(COLUMNS)[name]
    role = "dimension" if datatype in {"string", "date", "boolean"} else "measure"
    field_type = "ordinal" if datatype == "date" else (
        "nominal" if datatype in {"string", "boolean"} else "quantitative"
    )
    semantic = ""
    if name == "City":
        semantic = " semantic-role='[City].[Name]'"
    elif name == "CountyOrParish":
        semantic = " semantic-role='[County].[Name]'"
    elif name == "PostalCode":
        semantic = " semantic-role='[ZipCode].[Name]'"
    return (
        f"            <column datatype='{datatype}' name='[{name}]' "
        f"role='{role}'{semantic} type='{field_type}' />"
    )


def worksheet_xml(sheet: dict[str, object]) -> str:
    measure = str(sheet["measure"])
    instance = str(sheet["instance"])
    dependency_names = ["EventDate", "EventType", *FILTER_FIELDS, measure]
    dependency_names = list(dict.fromkeys(dependency_names))
    dependency_columns = "\n".join(dependency_column(name) for name in dependency_names)
    filter_instances = "\n".join(
        f"            <column-instance column='[{name}]' derivation='None' "
        f"name='[none:{name}:nk]' pivot='key' type='nominal' />"
        for name in ["EventType", *FILTER_FIELDS]
    )
    filters = []
    for group, name in enumerate(FILTER_FIELDS, start=1):
        filters.append(
            f"          <filter class='categorical' column='[{DATASOURCE}].[none:{name}:nk]' filter-group='{group}'>\n"
            f"            <groupfilter function='level-members' level='[none:{name}:nk]' user:ui-enumeration='all' user:ui-marker='enumerate' />\n"
            "          </filter>"
        )
    slices = [f"            <column>[{DATASOURCE}].[none:{name}:nk]</column>" for name in FILTER_FIELDS]
    if bool(sheet["closed_only"]):
        filters.append(
            f"          <filter class='categorical' column='[{DATASOURCE}].[none:EventType:nk]'>\n"
            "            <groupfilter function='member' level='[none:EventType:nk]' member='&quot;Closed Sale&quot;' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n"
            "          </filter>"
        )
        slices.append(f"            <column>[{DATASOURCE}].[none:EventType:nk]</column>")
    return f"""    <worksheet name='{xml_escape(str(sheet['name']))}'>
      <layout-options>
        <title><formatted-text><run>{xml_escape(str(sheet['name']))}</run></formatted-text></title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource caption='Week 8 Market Events' name='{DATASOURCE}' />
          </datasources>
          <datasource-dependencies datasource='{DATASOURCE}'>
{dependency_columns}
            <column-instance column='[EventDate]' derivation='Month-Trunc' name='[tmn:EventDate:qk]' pivot='key' type='quantitative' />
            <column-instance column='[{measure}]' derivation='{sheet['derivation']}' name='[{instance}]' pivot='key' type='quantitative' />
{filter_instances}
          </datasource-dependencies>
{chr(10).join(filters)}
          <slices>
{chr(10).join(slices)}
          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <format attr='title' class='0' field='[{DATASOURCE}].[{instance}]' scope='rows' value='{xml_escape(str(sheet['name']))}' />
            <format attr='title' class='0' field='[{DATASOURCE}].[tmn:EventDate:qk]' scope='cols' value='Month' />
          </style-rule>
          <style-rule element='label'>
            <format attr='text-format' field='[{DATASOURCE}].[{instance}]' value='{xml_escape(str(sheet['format']))}' />
          </style-rule>
          <style-rule element='worksheet'>
            <format attr='display-field-labels' scope='cols' value='false' />
            <format attr='display-field-labels' scope='rows' value='false' />
          </style-rule>
          <style-rule element='mark'>
            <encoding attr='color' field='[{DATASOURCE}].[{instance}]' type='palette'>
              <map to='{sheet['color']}'><bucket>&quot;[{DATASOURCE}].[{instance}]&quot;</bucket></map>
            </encoding>
          </style-rule>
        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view><breakdown value='auto' /></view>
            <mark class='Line' />
            <mark-sizing mark-sizing-setting='marks-scaling-off' />
            <style><style-rule element='mark'><format attr='mark-markers-mode' value='all' /></style-rule></style>
          </pane>
        </panes>
        <rows>[{DATASOURCE}].[{instance}]</rows>
        <cols>[{DATASOURCE}].[tmn:EventDate:qk]</cols>
      </table>
      <simple-id uuid='{new_uuid()}' />
    </worksheet>"""


def dashboard_xml() -> str:
    sheet_zones = [
        (SHEETS[0]["name"], 1, 0, 8000, 50000, 42000),
        (SHEETS[1]["name"], 2, 50000, 8000, 50000, 42000),
        (SHEETS[2]["name"], 3, 0, 50000, 33400, 42000),
        (SHEETS[3]["name"], 4, 33400, 50000, 33300, 42000),
        (SHEETS[4]["name"], 5, 66700, 50000, 33300, 42000),
    ]
    zones = [
        "        <zone h='100000' id='100' type-v2='layout-basic' w='100000' x='0' y='0'>",
        "          <zone h='7000' id='101' type-v2='title' w='100000' x='0' y='0' />",
    ]
    for name, zone_id, x, y, width, height in sheet_zones:
        zones.append(
            f"          <zone h='{height}' id='{zone_id}' name='{xml_escape(str(name))}' "
            f"w='{width}' x='{x}' y='{y}'><zone-style>"
            "<format attr='border-color' value='#d9d9d9' />"
            "<format attr='border-style' value='solid' />"
            "<format attr='border-width' value='1' />"
            "<format attr='margin' value='6' />"
            "</zone-style></zone>"
        )
    for offset, field in enumerate(FILTER_FIELDS):
        zones.append(
            f"          <zone h='6000' id='{20 + offset}' mode='dropdown' "
            f"name='{xml_escape(str(SHEETS[0]['name']))}' param='[{DATASOURCE}].[none:{field}:nk]' "
            f"type-v2='filter' w='24000' x='{1000 + offset * 24750}' y='93000'>"
            "<zone-style><format attr='border-color' value='#d9d9d9' />"
            "<format attr='border-style' value='solid' />"
            "<format attr='background-color' value='#ffffff' /></zone-style></zone>"
        )
    zones.append("        </zone>")
    return f"""    <dashboard enable-sort-zone-taborder='true' name='Market Overview'>
      <layout-options>
        <title><formatted-text><run fontname='Tableau Semibold' fontsize='18'>San Diego Residential Market Overview</run></formatted-text></title>
      </layout-options>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <datasources><datasource caption='Week 8 Market Events' name='{DATASOURCE}' /></datasources>
      <datasource-dependencies datasource='{DATASOURCE}'>
{chr(10).join(dependency_column(name) for name in FILTER_FIELDS)}
{chr(10).join(f"        <column-instance column='[{name}]' derivation='None' name='[none:{name}:nk]' pivot='key' type='nominal' />" for name in FILTER_FIELDS)}
      </datasource-dependencies>
      <zones>
{chr(10).join(zones)}
      </zones>
      <simple-id uuid='{new_uuid()}' />
    </dashboard>"""


def windows_xml() -> str:
    windows = [
    ]
    for sheet in SHEETS:
        name = xml_escape(str(sheet["name"]))
        windows.extend(
            [
                f"    <window class='worksheet' hidden='true' name='{name}'>",
                "      <cards>",
                "        <edge name='left'><strip size='180'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>",
                "        <edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip></edge>",
                "      </cards>",
                "      <viewpoint><zoom type='entire-view' /></viewpoint>",
                f"      <simple-id uuid='{new_uuid()}' />",
                "    </window>",
            ]
        )
    windows.extend(
        [
            "    <window class='dashboard' maximized='true' name='Market Overview'>",
            "      <viewpoints>",
            *[
                f"        <viewpoint name='{xml_escape(str(sheet['name']))}'><zoom type='entire-view' /></viewpoint>"
                for sheet in SHEETS
            ],
            "      </viewpoints>",
            "      <active id='-1' />",
            f"      <simple-id uuid='{new_uuid()}' />",
            "    </window>",
        ]
    )
    return "\n".join(windows)


def workbook_xml() -> str:
    worksheets = "\n".join(worksheet_xml(sheet) for sheet in SHEETS)
    return f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='18.1' source-build='2026.1.1 (20261.26.0410.0924)' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <AccessibleZoneTabOrder />
    <AnimationOnByDefault />
    <ObjectModelEncapsulateLegacy />
    <ObjectModelTableType />
    <SchemaViewerObjectModel />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences><preference name='ui.shelf.height' value='26' /></preferences>
  <datasources>
{datasource_xml()}
  </datasources>
  <worksheets>
{worksheets}
  </worksheets>
  <dashboards>
{dashboard_xml()}
  </dashboards>
  <windows source-height='30'>
{windows_xml()}
  </windows>
</workbook>
"""


def validate_csv(csv_path: Path) -> None:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Tableau source does not exist: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as source:
        header = next(csv.reader(source))
    expected = [name for name, _ in COLUMNS]
    if header != expected:
        raise ValueError(
            "The Tableau CSV header does not match the workbook schema.\n"
            f"Expected: {expected}\nActual: {header}"
        )


def convert_csv_value(value: str, datatype: str) -> object:
    """Convert one CSV cell to the matching Hyper value."""
    if value == "":
        return None
    if datatype == "string":
        return value
    if datatype == "date":
        return date.fromisoformat(value)
    if datatype == "integer":
        return int(value)
    if datatype == "real":
        return float(value)
    if datatype == "boolean":
        normalized = value.strip().lower()
        if normalized not in {"true", "false"}:
            raise ValueError(f"Invalid boolean value in Tableau source: {value!r}")
        return normalized == "true"
    raise ValueError(f"Unsupported Tableau datatype: {datatype}")


def create_hyper_extract(csv_path: Path, hyper_path: Path) -> int:
    """Create a Tableau Hyper extract from the prepared Week 8 CSV."""
    try:
        from tableauhyperapi import (
            Connection,
            CreateMode,
            HyperProcess,
            Inserter,
            Nullability,
            SqlType,
            TableDefinition,
            TableName,
            Telemetry,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Tableau Hyper API is required. Install it with: "
            "python3 -m pip install tableauhyperapi"
        ) from exc

    sql_types = {
        "string": SqlType.text(),
        "date": SqlType.date(),
        "integer": SqlType.big_int(),
        "real": SqlType.double(),
        "boolean": SqlType.bool(),
    }
    table_name = TableName("Extract", "Extract")
    table_definition = TableDefinition(
        table_name,
        [
            TableDefinition.Column(name, sql_types[datatype], Nullability.NULLABLE)
            for name, datatype in COLUMNS
        ],
    )
    hyper_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, "idx-week8") as hyper:
        with Connection(
            hyper.endpoint,
            hyper_path,
            CreateMode.CREATE_AND_REPLACE,
        ) as connection:
            connection.catalog.create_schema("Extract")
            connection.catalog.create_table(table_definition)
            with Inserter(connection, table_definition) as inserter:
                with csv_path.open(newline="", encoding="utf-8") as source:
                    reader = csv.reader(source)
                    next(reader)
                    for csv_row in reader:
                        if len(csv_row) != len(COLUMNS):
                            raise ValueError(
                                f"Row {row_count + 2:,} has {len(csv_row)} columns; "
                                f"expected {len(COLUMNS)}."
                            )
                        inserter.add_row(
                            [
                                convert_csv_value(value, datatype)
                                for value, (_, datatype) in zip(csv_row, COLUMNS)
                            ]
                        )
                        row_count += 1
                inserter.execute()
    return row_count


def build(csv_path: Path, output_path: Path) -> tuple[Path, Path]:
    validate_csv(csv_path)
    hyper_path = output_path.with_suffix(".hyper")
    row_count = create_hyper_extract(csv_path, hyper_path)
    xml = workbook_xml()
    ElementTree.fromstring(xml)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    twb_path = output_path.with_suffix(".twb")
    twb_path.write_text(xml, encoding="utf-8")
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.write(twb_path, "market_analysis.twb")
        archive.write(hyper_path, f"{HYPER_DIRECTORY}/{HYPER_TABLE}")
    with zipfile.ZipFile(output_path) as archive:
        required = {
            "market_analysis.twb",
            f"{HYPER_DIRECTORY}/{HYPER_TABLE}",
        }
        if not required.issubset(archive.namelist()):
            raise RuntimeError("Generated TWBX is missing required packaged files.")
        ElementTree.fromstring(archive.read("market_analysis.twb"))
    print(f"Extract rows: {row_count:,}")
    return twb_path, output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    twb_path, twbx_path = build(args.csv.resolve(), args.output.resolve())
    print(f"Created: {twb_path}")
    print(f"Created: {twbx_path}")
    print("Worksheets: 5")
    print("Dashboard: Market Overview")
    print("Shared filters: City, CountyOrParish, PostalCode, PropertySubType")


if __name__ == "__main__":
    main()
