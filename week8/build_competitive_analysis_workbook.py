"""Build the Weeks 8–10 Tableau Competitive Analysis packaged workbook.

The workbook contains four dynamic Top 100 rankings, two ZIP-code maps, and
five dashboards. Direct MLS event and listing identifiers are intentionally
excluded from the publishable Hyper extract.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import uuid
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_DIR / "outputs" / "week8" / "tableau_competitive_sales.csv"
DEFAULT_OUTPUT = PROJECT_DIR / "outputs" / "week8" / "competitive_analysis.twbx"
DEFAULT_PUBLISH_COPY = PROJECT_DIR / "week8" / "competitive_analysis.twbx"

DATASOURCE = "federated.week8competitiveanalysis"
CONNECTION = "hyper.week8competitivesales"
HYPER_TABLE = "competitive_analysis.hyper"
HYPER_DIRECTORY = "Data/competitive_analysis"
OBJECT_ID = "tableau_competitive_sales_csv"

SOURCE_COLUMNS = [
    ("EventId", "string"),
    ("CloseDate", "date"),
    ("Year", "integer"),
    ("Month", "integer"),
    ("YrMo", "string"),
    ("ListingKey", "string"),
    ("ListAgentFullName", "string"),
    ("ListOfficeName", "string"),
    ("BuyerOfficeName", "string"),
    ("PropertyType", "string"),
    ("PropertySubType", "string"),
    ("City", "string"),
    ("CountyOrParish", "string"),
    ("PostalCode", "string"),
    ("MLSAreaMajor", "string"),
    ("StateOrProvince", "string"),
    ("ClosePrice", "real"),
    ("SalesVolume", "real"),
    ("UnitsSold", "integer"),
    ("DaysOnMarket", "integer"),
    ("CloseToOriginalListRatio", "real"),
    ("CloseToOriginalListRatioOutlierFlag", "boolean"),
    ("CloseToOriginalListRatioEligible", "boolean"),
    ("PricePerSqFt", "real"),
    ("rate_30yr_fixed", "real"),
]

DIRECT_IDENTIFIER_FIELDS = {"EventId", "ListingKey"}
COLUMNS = [column for column in SOURCE_COLUMNS if column[0] not in DIRECT_IDENTIFIER_FIELDS]

# YrMo is the monthly control required by the rubric. Keeping one shared set
# on every worksheet makes dashboard filters apply consistently to all views.
FILTER_FIELDS = ["YrMo", "City", "CountyOrParish", "PostalCode", "PropertySubType"]

RANKING_SHEETS = [
    {
        "name": "Top 100 Listing Agents - Sales Volume",
        "dimension": "ListAgentFullName",
        "measure": "SalesVolume",
        "instance": "sum:SalesVolume:qk",
        "format": 'c"$"#,##0,,"M";(c"$"#,##0,,"M")',
        "axis": "Sales Volume",
        "color": "#4e79a7",
    },
    {
        "name": "Top 100 Listing Agents - Units Sold",
        "dimension": "ListAgentFullName",
        "measure": "UnitsSold",
        "instance": "sum:UnitsSold:qk",
        "format": "n#,##0",
        "axis": "Homes Sold",
        "color": "#59a14f",
    },
    {
        "name": "Top 100 Listing Offices - Sales Volume",
        "dimension": "ListOfficeName",
        "measure": "SalesVolume",
        "instance": "sum:SalesVolume:qk",
        "format": 'c"$"#,##0,,"M";(c"$"#,##0,,"M")',
        "axis": "Sales Volume",
        "color": "#f28e2b",
    },
    {
        "name": "Top 100 Listing Offices - Units Sold",
        "dimension": "ListOfficeName",
        "measure": "UnitsSold",
        "instance": "sum:UnitsSold:qk",
        "format": "n#,##0",
        "axis": "Homes Sold",
        "color": "#e15759",
    },
]

MAP_SHEETS = [
    {
        "name": "ZIP Median Close Price Map",
        "measure": "ClosePrice",
        "derivation": "Median",
        "instance": "median:ClosePrice:qk",
        "format": 'c"$"#,##0;(c"$"#,##0)',
        "legend": "Median Close Price",
        "palette": "tableau-map-blue-green-light",
    },
    {
        "name": "ZIP Homes Sold Map",
        "measure": "UnitsSold",
        "derivation": "Sum",
        "instance": "sum:UnitsSold:qk",
        "format": "n#,##0",
        "legend": "Homes Sold",
        "palette": "tableau-map-orange-light",
    },
]

ALL_SHEETS = RANKING_SHEETS + MAP_SHEETS
DASHBOARDS = [
    "Top 100 Listing Agents",
    "Top 100 Listing Offices",
    "ZIP Median Close Price",
    "ZIP Homes Sold",
    "Competitive Overview",
]


def xml_escape(value: str) -> str:
    """Escape a string used in workbook XML."""
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
    remote_types = {"string": "129", "date": "133", "integer": "20", "real": "5", "boolean": "16"}
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


def field_attributes(name: str, datatype: str) -> tuple[str, str, str]:
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
    elif name == "StateOrProvince":
        semantic = " semantic-role='[State].[Name]'"
    return role, field_type, semantic


def datasource_xml() -> str:
    top_columns = []
    for name, datatype in COLUMNS:
        role, field_type, semantic = field_attributes(name, datatype)
        default_format = ""
        if name in {"ClosePrice", "SalesVolume"}:
            default_format = " default-format='c&quot;$&quot;#,##0;(&quot;$&quot;#,##0)'"
        elif name == "CloseToOriginalListRatio":
            default_format = " default-format='p0.0%'"
        top_columns.append(
            f"      <column datatype='{datatype}'{default_format} name='[{xml_escape(name)}]' "
            f"role='{role}'{semantic} type='{field_type}' />"
        )
    return f"""    <datasource caption='Week 8 Competitive Sales' inline='true' name='{DATASOURCE}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='Week 8 Competitive Sales' name='{CONNECTION}'>
            <connection authentication='auth-none' author-locale='en_US' class='hyper' dbname='{HYPER_DIRECTORY}/{HYPER_TABLE}' default-settings='yes' port='' sslmode='' username='tableau_internal_user' />
          </named-connection>
        </named-connections>
        <relation connection='{CONNECTION}' name='Extract' table='[Extract].[Extract]' type='table' />
{metadata_records()}
      </connection>
      <aliases enabled='yes' />
{chr(10).join(top_columns)}
      <column caption='Week 8 Competitive Sales' datatype='table' name='[__tableau_internal_object_id__].[{OBJECT_ID}]' role='measure' type='quantitative' />
      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />
      <semantic-values>
        <semantic-value key='[Country].[Name]' value='&quot;United States&quot;' />
      </semantic-values>
      <object-graph>
        <objects>
          <object caption='Week 8 Competitive Sales' id='{OBJECT_ID}'>
            <properties context=''>
              <relation connection='{CONNECTION}' name='Extract' table='[Extract].[Extract]' type='table' />
            </properties>
          </object>
        </objects>
      </object-graph>
    </datasource>"""


def dependency_column(name: str) -> str:
    datatype = dict(COLUMNS)[name]
    role, field_type, semantic = field_attributes(name, datatype)
    return (
        f"            <column datatype='{datatype}' name='[{xml_escape(name)}]' "
        f"role='{role}'{semantic} type='{field_type}' />"
    )


def column_instance(name: str) -> str:
    return (
        f"            <column-instance column='[{xml_escape(name)}]' derivation='None' "
        f"name='[none:{xml_escape(name)}:nk]' pivot='key' type='nominal' />"
    )


def shared_filters_xml() -> tuple[str, str]:
    filters = []
    slices = []
    for group, name in enumerate(FILTER_FIELDS, start=1):
        filters.append(
            f"          <filter class='categorical' column='[{DATASOURCE}].[none:{name}:nk]' filter-group='{group}'>\n"
            f"            <groupfilter function='level-members' level='[none:{name}:nk]' user:ui-enumeration='all' user:ui-marker='enumerate' />\n"
            "          </filter>"
        )
        slices.append(f"            <column>[{DATASOURCE}].[none:{name}:nk]</column>")
    return "\n".join(filters), "\n".join(slices)


def ranking_worksheet_xml(sheet: dict[str, str]) -> str:
    dimension = sheet["dimension"]
    measure = sheet["measure"]
    instance = sheet["instance"]
    dependency_names = list(dict.fromkeys([*FILTER_FIELDS, dimension, measure]))
    dependencies = "\n".join(dependency_column(name) for name in dependency_names)
    filter_instances = "\n".join(column_instance(name) for name in FILTER_FIELDS)
    dimension_instance = f"none:{dimension}:nk"
    filters, slices = shared_filters_xml()
    top_filter = f"""          <filter class='categorical' column='[{DATASOURCE}].[{dimension_instance}]'>
            <groupfilter count='100' end='top' function='end' units='records' user:ui-marker='end' user:ui-top-by-field='true'>
              <groupfilter direction='DESC' expression='SUM([{measure}])' function='order' user:ui-marker='order'>
                <groupfilter function='level-members' level='[{dimension_instance}]' user:ui-enumeration='all' user:ui-marker='enumerate' />
              </groupfilter>
            </groupfilter>
          </filter>"""
    return f"""    <worksheet name='{xml_escape(sheet['name'])}'>
      <layout-options><title><formatted-text><run>{xml_escape(sheet['name'])}</run></formatted-text></title></layout-options>
      <table>
        <view>
          <datasources><datasource caption='Week 8 Competitive Sales' name='{DATASOURCE}' /></datasources>
          <datasource-dependencies datasource='{DATASOURCE}'>
{dependencies}
            <column-instance column='[{dimension}]' derivation='None' name='[{dimension_instance}]' pivot='key' type='nominal' />
            <column-instance column='[{measure}]' derivation='Sum' name='[{instance}]' pivot='key' type='quantitative' />
{filter_instances}
          </datasource-dependencies>
          <sort class='computed' column='[{DATASOURCE}].[{dimension_instance}]' direction='DESC' using='[{DATASOURCE}].[{instance}]' />
{filters}
{top_filter}
          <slices>
{slices}
            <column>[{DATASOURCE}].[{dimension_instance}]</column>
          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <format attr='title' class='0' field='[{DATASOURCE}].[{instance}]' scope='cols' value='{xml_escape(sheet['axis'])}' />
          </style-rule>
          <style-rule element='label'>
            <format attr='text-format' field='[{DATASOURCE}].[{instance}]' value='{xml_escape(sheet['format'])}' />
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
            <mark class='Bar' />
            <encodings><text column='[{DATASOURCE}].[{instance}]' /></encodings>
            <customized-tooltip>
              <formatted-text><run bold='true'>&lt;ATTR([{DATASOURCE}].[{dimension_instance}])&gt;</run><run>\n{xml_escape(sheet['axis'])}: &lt;SUM([{DATASOURCE}].[{measure}])&gt;</run></formatted-text>
            </customized-tooltip>
          </pane>
        </panes>
        <rows>[{DATASOURCE}].[{dimension_instance}]</rows>
        <cols>[{DATASOURCE}].[{instance}]</cols>
      </table>
      <simple-id uuid='{new_uuid()}' />
    </worksheet>"""


def map_worksheet_xml(sheet: dict[str, str]) -> str:
    measure = sheet["measure"]
    instance = sheet["instance"]
    dependency_names = list(dict.fromkeys([*FILTER_FIELDS, "StateOrProvince", measure]))
    dependencies = "\n".join(dependency_column(name) for name in dependency_names)
    filter_instances = "\n".join(column_instance(name) for name in FILTER_FIELDS)
    filters, slices = shared_filters_xml()
    return f"""    <worksheet name='{xml_escape(sheet['name'])}'>
      <layout-options><title><formatted-text><run>{xml_escape(sheet['name'])}</run></formatted-text></title></layout-options>
      <table>
        <view>
          <datasources><datasource caption='Week 8 Competitive Sales' name='{DATASOURCE}' /></datasources>
          <datasource-dependencies datasource='{DATASOURCE}'>
{dependencies}
            <column-instance column='[{measure}]' derivation='{sheet['derivation']}' name='[{instance}]' pivot='key' type='quantitative' />
{filter_instances}
          </datasource-dependencies>
{filters}
          <slices>
{slices}
          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='label'><format attr='text-format' field='[{DATASOURCE}].[{instance}]' value='{xml_escape(sheet['format'])}' /></style-rule>
          <style-rule element='map'>
            <format attr='washout' value='0.0' />
            <format attr='map-style' value='normal' />
            <format attr='wrap' value='true' />
          </style-rule>
          <style-rule element='map-data-layer'><format attr='palette' value='{sheet['palette']}' /></style-rule>
          <style-rule element='worksheet'>
            <format attr='display-field-labels' scope='cols' value='false' />
            <format attr='display-field-labels' scope='rows' value='false' />
          </style-rule>
        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view><breakdown value='auto' /></view>
            <mark class='Automatic' />
            <encodings>
              <color column='[{DATASOURCE}].[{instance}]' />
              <size column='[{DATASOURCE}].[{instance}]' />
              <lod column='[{DATASOURCE}].[none:PostalCode:nk]' />
            </encodings>
            <customized-tooltip>
              <formatted-text><run bold='true'>ZIP &lt;ATTR([{DATASOURCE}].[none:PostalCode:nk])&gt;</run><run>\n{xml_escape(sheet['legend'])}: &lt;AGG([{DATASOURCE}].[{measure}])&gt;</run></formatted-text>
            </customized-tooltip>
          </pane>
        </panes>
        <rows>[{DATASOURCE}].[Latitude (generated)]</rows>
        <cols>[{DATASOURCE}].[Longitude (generated)]</cols>
      </table>
      <simple-id uuid='{new_uuid()}' />
    </worksheet>"""


def dashboard_dependencies_xml() -> str:
    columns = "\n".join(dependency_column(name) for name in FILTER_FIELDS)
    instances = "\n".join(
        f"        <column-instance column='[{name}]' derivation='None' name='[none:{name}:nk]' pivot='key' type='nominal' />"
        for name in FILTER_FIELDS
    )
    return f"{columns}\n{instances}"


def filter_zone_xml(sheet_name: str, field: str, zone_id: int, x: int, y: int, width: int, height: int) -> str:
    return (
        f"          <zone h='{height}' id='{zone_id}' mode='dropdown' name='{xml_escape(sheet_name)}' "
        f"param='[{DATASOURCE}].[none:{field}:nk]' type-v2='filter' w='{width}' x='{x}' y='{y}'>"
        "<zone-style><format attr='border-color' value='#d9d9d9' />"
        "<format attr='border-style' value='solid' /><format attr='background-color' value='#ffffff' />"
        "</zone-style></zone>"
    )


def sheet_zone_xml(sheet_name: str, zone_id: int, x: int, y: int, width: int, height: int) -> str:
    return (
        f"          <zone h='{height}' id='{zone_id}' name='{xml_escape(sheet_name)}' w='{width}' x='{x}' y='{y}'>"
        "<zone-style><format attr='border-color' value='#d9d9d9' /><format attr='border-style' value='solid' />"
        "<format attr='border-width' value='1' /><format attr='margin' value='6' /></zone-style></zone>"
    )


def filters_for_dashboard(anchor_sheet: str, start_id: int = 20) -> list[str]:
    return [
        filter_zone_xml(anchor_sheet, field, start_id + offset, 81500, 11000 + offset * 16500, 17500, 10500)
        for offset, field in enumerate(FILTER_FIELDS)
    ]


def pair_dashboard_xml(name: str, title: str, left_sheet: str, right_sheet: str) -> str:
    zones = [
        "        <zone h='100000' id='100' type-v2='layout-basic' w='100000' x='0' y='0'>",
        "          <zone h='7500' id='101' type-v2='title' w='100000' x='0' y='0' />",
        sheet_zone_xml(left_sheet, 1, 0, 8000, 40250, 91000),
        sheet_zone_xml(right_sheet, 2, 40250, 8000, 40250, 91000),
        *filters_for_dashboard(left_sheet),
        "        </zone>",
    ]
    return f"""    <dashboard enable-sort-zone-taborder='true' name='{xml_escape(name)}'>
      <layout-options><title><formatted-text><run fontname='Tableau Semibold' fontsize='18'>{xml_escape(title)}</run></formatted-text></title></layout-options>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <datasources><datasource caption='Week 8 Competitive Sales' name='{DATASOURCE}' /></datasources>
      <datasource-dependencies datasource='{DATASOURCE}'>
{dashboard_dependencies_xml()}
      </datasource-dependencies>
      <zones>
{chr(10).join(zones)}
      </zones>
      <simple-id uuid='{new_uuid()}' />
    </dashboard>"""


def map_dashboard_xml(name: str, title: str, sheet_name: str) -> str:
    zones = [
        "        <zone h='100000' id='100' type-v2='layout-basic' w='100000' x='0' y='0'>",
        "          <zone h='7500' id='101' type-v2='title' w='100000' x='0' y='0' />",
        sheet_zone_xml(sheet_name, 1, 0, 8000, 80500, 91000),
        *filters_for_dashboard(sheet_name),
        "        </zone>",
    ]
    return f"""    <dashboard enable-sort-zone-taborder='true' name='{xml_escape(name)}'>
      <layout-options><title><formatted-text><run fontname='Tableau Semibold' fontsize='18'>{xml_escape(title)}</run></formatted-text></title></layout-options>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <datasources><datasource caption='Week 8 Competitive Sales' name='{DATASOURCE}' /></datasources>
      <datasource-dependencies datasource='{DATASOURCE}'>
{dashboard_dependencies_xml()}
      </datasource-dependencies>
      <zones>
{chr(10).join(zones)}
      </zones>
      <simple-id uuid='{new_uuid()}' />
    </dashboard>"""


def overview_dashboard_xml() -> str:
    anchor = RANKING_SHEETS[0]["name"]
    zones = [
        "        <zone h='100000' id='100' type-v2='layout-basic' w='100000' x='0' y='0'>",
        "          <zone h='6500' id='101' type-v2='title' w='100000' x='0' y='0' />",
        sheet_zone_xml(RANKING_SHEETS[0]["name"], 1, 0, 7000, 40500, 45500),
        sheet_zone_xml(RANKING_SHEETS[2]["name"], 2, 40500, 7000, 40500, 45500),
        sheet_zone_xml(MAP_SHEETS[0]["name"], 3, 0, 52500, 40500, 47000),
        sheet_zone_xml(MAP_SHEETS[1]["name"], 4, 40500, 52500, 40500, 47000),
        *filters_for_dashboard(anchor),
        "        </zone>",
    ]
    return f"""    <dashboard enable-sort-zone-taborder='true' name='Competitive Overview'>
      <layout-options><title><formatted-text><run fontname='Tableau Semibold' fontsize='18'>San Diego Residential Competitive Overview</run></formatted-text></title></layout-options>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' sizing-mode='fixed' />
      <datasources><datasource caption='Week 8 Competitive Sales' name='{DATASOURCE}' /></datasources>
      <datasource-dependencies datasource='{DATASOURCE}'>
{dashboard_dependencies_xml()}
      </datasource-dependencies>
      <zones>
{chr(10).join(zones)}
      </zones>
      <simple-id uuid='{new_uuid()}' />
    </dashboard>"""


def windows_xml() -> str:
    windows = []
    for sheet in ALL_SHEETS:
        name = xml_escape(sheet["name"])
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
    viewpoints = {
        "Top 100 Listing Agents": [RANKING_SHEETS[0]["name"], RANKING_SHEETS[1]["name"]],
        "Top 100 Listing Offices": [RANKING_SHEETS[2]["name"], RANKING_SHEETS[3]["name"]],
        "ZIP Median Close Price": [MAP_SHEETS[0]["name"]],
        "ZIP Homes Sold": [MAP_SHEETS[1]["name"]],
        "Competitive Overview": [RANKING_SHEETS[0]["name"], RANKING_SHEETS[2]["name"], MAP_SHEETS[0]["name"], MAP_SHEETS[1]["name"]],
    }
    for dashboard in DASHBOARDS:
        maximized = " maximized='true'" if dashboard == "Competitive Overview" else ""
        windows.append(f"    <window class='dashboard'{maximized} name='{xml_escape(dashboard)}'>")
        windows.append("      <viewpoints>")
        windows.extend(
            f"        <viewpoint name='{xml_escape(sheet)}'><zoom type='entire-view' /></viewpoint>"
            for sheet in viewpoints[dashboard]
        )
        windows.extend(
            [
                "      </viewpoints>",
                "      <active id='-1' />",
                f"      <simple-id uuid='{new_uuid()}' />",
                "    </window>",
            ]
        )
    return "\n".join(windows)


def workbook_xml() -> str:
    worksheets = "\n".join(ranking_worksheet_xml(sheet) for sheet in RANKING_SHEETS)
    worksheets += "\n" + "\n".join(map_worksheet_xml(sheet) for sheet in MAP_SHEETS)
    dashboards = "\n".join(
        [
            pair_dashboard_xml(
                "Top 100 Listing Agents",
                "Top 100 Listing Agents by Sales Volume and Units",
                RANKING_SHEETS[0]["name"],
                RANKING_SHEETS[1]["name"],
            ),
            pair_dashboard_xml(
                "Top 100 Listing Offices",
                "Top 100 Listing Offices by Sales Volume and Units",
                RANKING_SHEETS[2]["name"],
                RANKING_SHEETS[3]["name"],
            ),
            map_dashboard_xml("ZIP Median Close Price", "Median Close Price by ZIP Code", MAP_SHEETS[0]["name"]),
            map_dashboard_xml("ZIP Homes Sold", "Homes Sold by ZIP Code", MAP_SHEETS[1]["name"]),
            overview_dashboard_xml(),
        ]
    )
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
{dashboards}
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
    expected = [name for name, _ in SOURCE_COLUMNS]
    if header != expected:
        raise ValueError(
            "The Tableau CSV header does not match the competitive workbook schema.\n"
            f"Expected: {expected}\nActual: {header}"
        )


def convert_csv_value(value: str, datatype: str) -> object:
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
            "Tableau Hyper API is required. Install it with: python3 -m pip install tableauhyperapi"
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
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU, "idx-week8-competitive") as hyper:
        with Connection(hyper.endpoint, hyper_path, CreateMode.CREATE_AND_REPLACE) as connection:
            connection.catalog.create_schema("Extract")
            connection.catalog.create_table(table_definition)
            with Inserter(connection, table_definition) as inserter:
                with csv_path.open(newline="", encoding="utf-8") as source:
                    reader = csv.reader(source)
                    header = next(reader)
                    source_indexes = {name: header.index(name) for name, _ in COLUMNS}
                    for csv_row in reader:
                        if len(csv_row) != len(SOURCE_COLUMNS):
                            raise ValueError(
                                f"Row {row_count + 2:,} has {len(csv_row)} columns; expected {len(SOURCE_COLUMNS)}."
                            )
                        inserter.add_row(
                            [
                                convert_csv_value(csv_row[source_indexes[name]], datatype)
                                for name, datatype in COLUMNS
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
        archive.write(twb_path, "competitive_analysis.twb")
        archive.write(hyper_path, f"{HYPER_DIRECTORY}/{HYPER_TABLE}")
    with zipfile.ZipFile(output_path) as archive:
        required = {"competitive_analysis.twb", f"{HYPER_DIRECTORY}/{HYPER_TABLE}"}
        if not required.issubset(archive.namelist()):
            raise RuntimeError("Generated TWBX is missing required packaged files.")
        ElementTree.fromstring(archive.read("competitive_analysis.twb"))
    print(f"Extract rows: {row_count:,}")
    return twb_path, output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--publish-copy",
        type=Path,
        nargs="?",
        const=DEFAULT_PUBLISH_COPY,
        help=(
            "also copy the packaged workbook to a tracked deliverable path; "
            "defaults to week8/competitive_analysis.twbx"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    twb_path, twbx_path = build(args.csv.resolve(), args.output.resolve())
    if args.publish_copy:
        publish_path = args.publish_copy.resolve()
        publish_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(twbx_path, publish_path)
        print(f"Created publish copy: {publish_path}")
    print(f"Created: {twb_path}")
    print(f"Created: {twbx_path}")
    print("Worksheets: 6")
    print("Dashboards: 4 required + Competitive Overview custom dashboard")
    print("Shared filters: YrMo, City, CountyOrParish, PostalCode, PropertySubType")


if __name__ == "__main__":
    main()
