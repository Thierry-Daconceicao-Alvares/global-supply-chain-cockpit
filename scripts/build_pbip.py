"""Write the Power BI project (PBIP) of the Global Supply Chain Cockpit.

Two plain-text items, written to powerbi/:
- GlobalSupplyChainCockpit.SemanticModel: TMDL, tables loaded from the Parquet
  files of the data folder (Power Query parameter DataFolder);
- GlobalSupplyChainCockpit.Report: PBIR report, 5 pages + a drill-through page +
  a tooltip page, drawn over background images (build/backgrounds/).

Usage: python scripts/build_pbip.py [--data-folder "C:\\path\\to\\repo\\data"]
"""
from __future__ import annotations

import json
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from layout import *  # noqa: E402,F401,F403

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi"
NAME = "GlobalSupplyChainCockpit"
NS = uuid.UUID("7d41c2a9-5e3b-4f6a-8b1c-2e9f0a7d6c35")
SCHEMAS = "https://developer.microsoft.com/json-schemas/fabric"
VISUAL_SCHEMA = f"{SCHEMAS}/item/report/definition/visualContainer/2.2.0/schema.json"
PAGE_SCHEMA = f"{SCHEMAS}/item/report/definition/page/2.0.0/schema.json"
REPORT_SCHEMA = f"{SCHEMAS}/item/report/definition/report/3.0.0/schema.json"
BASE_THEME = "CY24SU10"
BASE_THEME_SRC = ROOT / "scripts" / "assets" / "CY24SU10.json"
THEME_FILE = "GlobalSupplyChainCockpit.json"
DEFAULT_FOLDER = r"C:\GlobalSupplyChainCockpit\data"  # change it with --data-folder or in Power BI
M = "_Measures"
BG_DIR = ROOT / "build" / "backgrounds"
FONT = "Segoe UI"
FONT_SB = "Segoe UI Semibold"


def tag(*parts: str) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


def quote(name: str) -> str:
    if name.replace("_", "a").isalnum() and not name[0].isdigit():
        return name
    return "'" + name.replace("'", "''") + "'"


def tmdl_text(value: str) -> str:
    if '"' in value or value != value.strip():
        return '"' + value.replace('"', '""') + '"'
    return value


# ------------------------------------------------------------------ semantic model


@dataclass
class Col:
    name: str
    dtype: str
    fmt: str | None = None
    summarize: str = "none"
    hidden: bool = False
    key: bool = False
    sort_by: str | None = None
    desc: str | None = None
    category: str | None = None


@dataclass
class Table:
    name: str
    desc: str
    cols: list[Col]
    file: str
    date_table: bool = False


def s(n, desc=None, hidden=False, sort_by=None):
    return Col(n, "string", hidden=hidden, desc=desc, sort_by=sort_by)


def i(n, desc=None, hidden=False, summarize="none", fmt="0"):
    return Col(n, "int64", fmt=fmt, hidden=hidden, desc=desc, summarize=summarize)


def f(n, fmt="#,0.00", desc=None, hidden=False, summarize="sum"):
    return Col(n, "double", fmt=fmt, hidden=hidden, desc=desc, summarize=summarize)


def d(n, desc=None, hidden=False, key=False, fmt="dd mmm yyyy"):
    return Col(n, "dateTime", fmt=fmt, hidden=hidden, desc=desc, key=key)


TABLES = [
    Table("Sales", "One row per order line (DataCo Smart Supply Chain, January 2015 to September 2017).", [
        i("order_item_id", "Order line number.", hidden=True),
        i("order_id", "Order number."),
        d("order_date", "Order date."), d("ship_date", "Shipping date."),
        i("customer_id", hidden=True), i("product_id", hidden=True),
        s("country", hidden=True), s("market", hidden=True), s("region", hidden=True),
        s("shipping_mode", hidden=True),
        s("delivery_status", "Delivery status as recorded."), s("order_status", "Order status as recorded."),
        s("payment_type", "Payment type."), s("segment", "Customer segment."),
        i("quantity", "Units ordered.", summarize="sum", fmt="#,0"),
        f("gross_sales_amt", "$#,0", hidden=True), f("discount_amt", "$#,0", hidden=True),
        f("revenue_amt", "$#,0", hidden=True), f("profit_amt", "$#,0", hidden=True),
        i("days_real", "Actual shipping days."), i("days_scheduled", "Scheduled shipping days."),
        i("is_late", hidden=True, summarize="sum"), i("is_cancelled", hidden=True, summarize="sum"),
        i("is_fraud", hidden=True, summarize="sum"),
        i("delay_days", "Actual minus scheduled shipping days."),
        i("is_loss", hidden=True, summarize="sum"), i("shipped", hidden=True, summarize="sum"),
    ], "sales.parquet"),
    Table("Geography", "Countries of delivery, with their region and market.", [
        Col("country", "string", desc="Country of delivery.", category="Country"),
        s("market", hidden=True), s("region", "Region of delivery."),
    ], "geography.parquet"),
    Table("Markets", "The five markets.", [
        s("market", hidden=True), s("market_label", "Market.", sort_by="market_order"), i("market_order", hidden=True),
    ], "markets.parquet"),
    Table("Products", "Products, categories and departments.", [
        i("product_id", hidden=True), s("product", "Product."), s("category", "Product category."),
        s("department", "Department."), f("list_price", "$#,0.00", "List price.", summarize="none"),
    ], "products.parquet"),
    Table("ShippingModes", "Shipping modes and the shipping days they promise.", [
        s("shipping_mode", "Shipping mode.", sort_by="mode_order"), i("mode_order", hidden=True),
        i("promised_days", "Scheduled shipping days."),
    ], "shipping_modes.parquet"),
    Table("Dates", "Calendar, January 2015 to September 2017.", [
        d("date", key=True), i("year", "Calendar year."), s("quarter"), s("year_quarter", "Year and quarter."),
        i("month_number", hidden=True), s("month", sort_by="month_number"),
        d("month_start", "First day of the month.", fmt="mmm yyyy"),
    ], "dates.parquet", date_table=True),
]
RELATIONSHIPS = [
    ("Sales", "country", "Geography", "country"),
    ("Geography", "market", "Markets", "market"),
    ("Sales", "product_id", "Products", "product_id"),
    ("Sales", "shipping_mode", "ShippingModes", "shipping_mode"),
    ("Sales", "order_date", "Dates", "date"),
]


@dataclass
class Measure:
    name: str
    expr: str
    fmt: str
    folder: str
    desc: str


MONEY_M = '$#,0'
MONEY_MEASURES = {'Revenue', 'Profit', 'Gross Sales', 'Discounts', 'Revenue Delivered Late', 'Fraud Revenue', 'Cancelled Revenue', 'Loss Amount'}
MONEY_K = '$#,0.0,"K"'


def ins_guard(body):
    return body


MEASURES = [
    Measure("Revenue", "SUM ( Sales[revenue_amt] )", MONEY_M, "Sales", "Sales net of discounts."),
    Measure("Gross Sales", "SUM ( Sales[gross_sales_amt] )", MONEY_M, "Sales", "Sales before discounts."),
    Measure("Discounts", "SUM ( Sales[discount_amt] )", MONEY_M, "Sales", "Discounts granted."),
    Measure("Discount Rate", "DIVIDE ( [Discounts], [Gross Sales] )", "0.0%", "Sales", "Discounts / gross sales."),
    Measure("Profit", "SUM ( Sales[profit_amt] )", MONEY_M, "Sales", "Profit as given in the source."),
    Measure("Profit Margin", "DIVIDE ( [Profit], [Revenue] )", "0.0%", "Sales", "Profit / revenue."),
    Measure("Orders", "DISTINCTCOUNT ( Sales[order_id] )", "#,0", "Sales", "Number of orders."),
    Measure("Items", "SUM ( Sales[quantity] )", "#,0", "Sales", "Units ordered."),
    Measure("Items per Order", "DIVIDE ( [Items], [Orders] )", "0.00", "Sales", "Units per order."),
    Measure("Customers", "DISTINCTCOUNT ( Sales[customer_id] )", "#,0", "Sales", "Distinct customers."),
    Measure("Avg Order Value", "DIVIDE ( [Revenue], [Orders] )", "$#,0", "Sales", "Revenue per order."),
    Measure("Revenue per Customer", "DIVIDE ( [Revenue], [Customers] )", "$#,0", "Sales", "Revenue per customer."),
    Measure("Loss Lines %", "DIVIDE ( CALCULATE ( COUNTROWS ( Sales ), Sales[is_loss] = 1 ), COUNTROWS ( Sales ) )",
            "0.0%", "Sales", "Share of order lines sold at a loss."),
    Measure("Loss Amount", "- CALCULATE ( SUM ( Sales[profit_amt] ), Sales[is_loss] = 1 )", MONEY_M, "Sales",
            "Losses on the lines sold below cost (positive number)."),
    # Delivery
    Measure("Shipped Orders", "CALCULATE ( DISTINCTCOUNT ( Sales[order_id] ), Sales[shipped] = 1 )", "#,0",
            "Delivery", "Orders whose shipment was not cancelled."),
    Measure("Late Orders", "CALCULATE ( DISTINCTCOUNT ( Sales[order_id] ), Sales[is_late] = 1 )", "#,0",
            "Delivery", "Orders delivered after the scheduled date."),
    Measure("Late Rate", "DIVIDE ( [Late Orders], [Shipped Orders] )", "0.0%", "Delivery",
            "Share of shipped orders delivered late."),
    Measure("Tolerance Value", "SELECTEDVALUE ( 'Delay Tolerance'[Delay Tolerance], 0 )", "0", "Delivery",
            "Days of delay still counted as on time (what-if, 0 by default)."),
    Measure("On Time Within Tolerance",
            "VAR t = [Tolerance Value]\nRETURN\n    DIVIDE (\n"
            "        COALESCE ( CALCULATE ( DISTINCTCOUNT ( Sales[order_id] ), Sales[shipped] = 1, Sales[delay_days] <= t ), 0 ),\n"
            "        [Shipped Orders]\n    )",
            "0.0%", "Delivery", "Share of shipped orders delivered within the scheduled days plus the tolerance."),
    Measure("Avg Delay Late", "CALCULATE ( AVERAGE ( Sales[delay_days] ), Sales[is_late] = 1 )", '0.0" days"',
            "Delivery", "Average days of delay of the late orders."),
    Measure("Avg Days Scheduled", "CALCULATE ( AVERAGE ( Sales[days_scheduled] ), Sales[shipped] = 1 )",
            '0.0" d"', "Delivery", "Average scheduled shipping days."),
    Measure("Avg Days Real", "CALCULATE ( AVERAGE ( Sales[days_real] ), Sales[shipped] = 1 )", '0.0" d"',
            "Delivery", "Average actual shipping days."),
    Measure("Revenue Delivered Late", "CALCULATE ( [Revenue], Sales[is_late] = 1 )", MONEY_M, "Delivery",
            "Revenue of the orders delivered late."),
    Measure("Cancelled Orders", "CALCULATE ( DISTINCTCOUNT ( Sales[order_id] ), Sales[is_cancelled] = 1 )", "#,0",
            "Delivery", "Orders whose shipment was cancelled."),
    Measure("Cancelled Revenue", "CALCULATE ( [Revenue], Sales[is_cancelled] = 1 )", MONEY_M, "Delivery",
            "Revenue of the cancelled shipments."),
    # Fraud
    Measure("Fraud Orders", "CALCULATE ( DISTINCTCOUNT ( Sales[order_id] ), Sales[is_fraud] = 1 )", "#,0", "Risk",
            "Orders with the status Suspected fraud."),
    Measure("Fraud Rate", "DIVIDE ( COALESCE ( [Fraud Orders], 0 ), [Orders] )", "0.0%", "Risk", "Share of orders suspected of fraud."),
    Measure("Fraud Revenue", "CALCULATE ( [Revenue], Sales[is_fraud] = 1 )", MONEY_M, "Risk",
            "Revenue of the orders suspected of fraud."),
    Measure("Fraud Rate Transfers", 'CALCULATE ( [Fraud Rate], Sales[payment_type] = "Transfer" )', "0.0%", "Risk",
            "Share of bank-transfer orders suspected of fraud."),
    # Colours
    Measure("Late Color",
            'VAR r = [Late Rate]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( r ), "#CBD5E1", r >= 0.7, "#E5484D",'
            ' r >= 0.5, "#F5A524", "#12A594" )', "", "Colours", "Red from 70% late, amber from 50%, green below."),
    Measure("Margin Heat Color",
            'VAR m = [Profit Margin]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( m ), "#FFFFFF", m >= 0.125, "#0B7A6A",'
            ' m >= 0.12, "#2FA898", m >= 0.115, "#A5E0D6", "#E6F5F2" )', "", "Colours", "Heatmap colour of the margin."),
    Measure("Margin Heat Font", 'IF ( [Profit Margin] >= 0.12, "#FFFFFF", "#14213D" )', "", "Colours",
            "Text colour on the heatmap."),
    Measure("Margin Color",
            'VAR m = [Profit Margin]\nRETURN\n    SWITCH ( TRUE (), ISBLANK ( m ), "#CBD5E1", m < 0, "#E5484D",'
            ' m < 0.1, "#F5A524", "#12A594" )', "", "Colours", "Red below 0, amber below 10%, green above."),
    # Labels
    Measure("Selected Country", 'SELECTEDVALUE ( Geography[country], "All countries" )', "", "Labels",
            "Country in context."),
    # Insights
    Measure("Insight Delivery",
            "VAR t = TOPN ( 1, ALLSELECTED ( ShippingModes[shipping_mode] ), [Late Rate], DESC )\n"
            "VAR n = MAXX ( t, ShippingModes[shipping_mode] )\n"
            "VAR r = CALCULATE ( [Late Rate], ShippingModes[shipping_mode] = n )\n"
            "VAR sc = CALCULATE ( [Avg Days Scheduled], ShippingModes[shipping_mode] = n )\n"
            "VAR rl = CALCULATE ( [Avg Days Real], ShippingModes[shipping_mode] = n )\n"
            "RETURN\n    IF ( ISBLANK ( n ), \"No data in this selection\",\n"
            "        n & \": \" & FORMAT ( r, \"0%\" ) & \" late, \" & FORMAT ( sc, \"0\" ) & \" day promised, \" & FORMAT ( rl, \"0.0\" ) & \" taken\" )",
            "", "Insights", "Shipping mode with the highest late rate."),
    Measure("Insight Geography",
            "VAR lo = MINX ( ALLSELECTED ( Geography[region] ), [Late Rate] )\n"
            "VAR hi = MAXX ( ALLSELECTED ( Geography[region] ), [Late Rate] )\n"
            "RETURN\n    IF ( ISBLANK ( hi ), \"No data in this selection\",\n"
            "        \"Every region is late on \" & FORMAT ( lo, \"0%\" ) & \" to \" & FORMAT ( hi, \"0%\" )"
            " & \" of orders: geography is not the cause, the shipping promise is.\" )",
            "", "Insights", "Range of late rates across regions."),
    Measure("Insight Margin",
            "VAR l = [Loss Amount]\nVAR p = [Profit]\nVAR s = [Loss Lines %]\nRETURN\n"
            "    IF ( ISBLANK ( p ), \"No data in this selection\",\n"
            "        FORMAT ( s, \"0%\" ) & \" of lines sold below cost: -\" & FORMAT ( l / 1000000, \"$#,0.0\" )"
            " & \"M vs \" & FORMAT ( p / 1000000, \"$#,0.0\" ) & \"M profit\" )",
            "", "Insights", "Losses on lines sold below cost, compared with total profit."),
    Measure("Insight Fraud",
            "VAR f = [Fraud Orders]\nVAR ft = CALCULATE ( [Fraud Orders], Sales[payment_type] = \"Transfer\" )\n"
            "RETURN\n    IF ( ISBLANK ( f ), \"No suspected fraud in this selection\",\n"
            "        FORMAT ( DIVIDE ( ft, f ), \"0%\" ) & \" by transfer · \""
            " & FORMAT ( [Fraud Rate Transfers], \"0.0%\" ) & \" of transfers flagged\" )",
            "", "Insights", "Concentration of suspected fraud on bank transfers."),
]



def describe(text_, indent):
    return [f"{indent}/// {text_}"] if text_ else []


def render_table(t: Table) -> str:
    out = describe(t.desc, "") + [f"table {quote(t.name)}"]
    if t.date_table:
        out += ["\tdataCategory: Time"]
    out += [f"\tlineageTag: {tag('table', t.name)}", ""]
    for c in t.cols:
        out += describe(c.desc, "\t")
        out += [f"\tcolumn {quote(c.name)}", f"\t\tdataType: {c.dtype}"]
        if c.hidden:
            out += ["\t\tisHidden"]
        if c.key:
            out += ["\t\tisKey"]
        if c.category:
            out += [f"\t\tdataCategory: {c.category}"]
        if c.fmt:
            out += [f"\t\tformatString: {tmdl_text(c.fmt)}"]
        out += [f"\t\tlineageTag: {tag('column', t.name, c.name)}", f"\t\tsummarizeBy: {c.summarize}",
                f"\t\tsourceColumn: {c.name}"]
        if c.sort_by:
            out += [f"\t\tsortByColumn: {quote(c.sort_by)}"]
        out += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
        if c.dtype == "dateTime":
            out += ["\t\tannotation UnderlyingDateTimeDataType = Date", ""]
    src = ["let", '    Root = Text.TrimEnd(DataFolder, "\\") & "\\",',
           f'    Source = Parquet.Document(File.Contents(Root & "{t.file}"))', "in", "    Source"]
    out += [f"\tpartition {quote(t.name)} = m", "\t\tmode: import", "\t\tsource ="]
    out += ["\t\t\t\t" + line for line in src]
    out += ["", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def render_sla_table() -> str:
    return "\n".join([
        "/// What-if parameter: days of delay still counted as on time.",
        "table 'Delay Tolerance'",
        f"\tlineageTag: {tag('table', 'Delay Tolerance')}",
        "",
        "\tcolumn 'Delay Tolerance'",
        "\t\tdataType: int64",
        "\t\tformatString: 0",
        f"\t\tlineageTag: {tag('column', 'Delay Tolerance', 'Delay Tolerance')}",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: [Value]",
        "",
        "\t\tannotation SummarizationSetBy = User",
        "",
        "\tpartition 'Delay Tolerance' = calculated",
        "\t\tmode: import",
        "\t\tsource = GENERATESERIES ( 0, 3, 1 )",
        "",
    ])


def render_measures() -> str:
    out = ["/// Measures of the report, grouped in display folders.", f"table {M}",
           f"\tlineageTag: {tag('table', M)}", ""]
    for m in MEASURES:
        out += describe(m.desc, "\t")
        lines = m.expr.splitlines()
        if len(lines) == 1:
            out += [f"\tmeasure {quote(m.name)} = {lines[0]}"]
        else:
            out += [f"\tmeasure {quote(m.name)} ="] + ["\t\t\t" + ln for ln in lines]
        if m.fmt:
            out += [f"\t\tformatString: {tmdl_text(m.fmt)}"]
        out += [f"\t\tdisplayFolder: {m.folder}", f"\t\tlineageTag: {tag('measure', m.name)}", ""]
    out += ["\tcolumn Value", "\t\tisHidden", f"\t\tlineageTag: {tag('column', M, 'Value')}",
            "\t\tsummarizeBy: none", "\t\tisNameInferred", "\t\tsourceColumn: [Value]", "",
            "\t\tannotation SummarizationSetBy = Automatic", "",
            f"\tpartition {M} = calculated", "\t\tmode: import", '\t\tsource = ROW ( "Value", BLANK () )', ""]
    return "\n".join(out)


def write_model():
    item = OUT / f"{NAME}.SemanticModel"
    de = item / "definition"
    (de / "tables").mkdir(parents=True)
    wjson(item / "definition.pbism", {
        "$schema": f"{SCHEMAS}/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})
    wtext(de / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    names = [t.name for t in TABLES] + ["Delay Tolerance", M]
    order = json.dumps(["DataFolder", *[t.name for t in TABLES]])
    wtext(de / "model.tmdl", "\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        f"annotation PBI_QueryOrder = {order}", "", "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_ProTooling = ["DevMode"]', "", *[f"ref table {quote(n)}" for n in names], ""]))
    wtext(de / "expressions.tmdl", "\n".join([
        "/// Folder of the Parquet files (the data folder next to the .pbip file).",
        f'expression DataFolder = "{DEFAULT_FOLDER}" meta [IsParameterQuery=true, Type="Text", '
        "IsParameterQueryRequired=true]",
        f"\tlineageTag: {tag('expression', 'DataFolder')}", "", "\tannotation PBI_ResultType = Text", ""]))
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {tag('rel', ft, fc, tt)}", f"\tfromColumn: {quote(ft)}.{quote(fc)}",
                f"\ttoColumn: {quote(tt)}.{quote(tc)}", ""]
    wtext(de / "relationships.tmdl", "\n".join(rel))
    for t in TABLES:
        wtext(de / "tables" / f"{t.name}.tmdl", render_table(t))
    wtext(de / "tables" / "Delay Tolerance.tmdl", render_sla_table())
    wtext(de / "tables" / f"{M}.tmdl", render_measures())


# -------------------------------------------------------------------------- report


def lit(v):
    if isinstance(v, bool):
        t = "true" if v else "false"
    elif isinstance(v, int | float):
        t = f"{v}D"
    else:
        t = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": t}}}


def color(c):
    return {"solid": {"color": lit(c)}}


def col(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def mea(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": prop}}


def proj(field_, display=None, active=None):
    kind = "Column" if "Column" in field_ else "Measure"
    ent = field_[kind]["Expression"]["SourceRef"]["Entity"]
    prop = field_[kind]["Property"]
    item = {"field": field_, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if display:
        item["displayName"] = display
    if active is not None:
        item["active"] = active
    return item


def measure_color(name):
    """Conditional formatting by field value (a measure returning a hex colour)."""
    return {"solid": {"color": {"expr": mea(name)}}}


ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def props(**kw):
    return [{"properties": kw}]


@dataclass
class V:
    name: str
    vtype: str
    x: float
    y: float
    w: float
    h: float
    roles: dict = field(default_factory=dict)
    sort: list = field(default_factory=list)
    objects: dict = field(default_factory=dict)
    vco: dict = field(default_factory=dict)
    filters: list = field(default_factory=list)
    sync: str | None = None
    tooltip_page: bool = False

    def to_json(self, z):
        visual = {"visualType": self.vtype}
        if self.roles:
            q = {"queryState": {r: {"projections": p} for r, p in self.roles.items()}}
            if self.sort:
                q["sortDefinition"] = {"sort": [{"field": fl, "direction": dr} for fl, dr in self.sort],
                                       "isDefaultSort": False}
            visual["query"] = q
        if self.objects:
            visual["objects"] = self.objects
        vco = {
            "background": props(show=lit(False)),
            "border": props(show=lit(False)),
            "title": props(show=lit(False)),
            "visualHeader": props(show=lit(False)),
            "dropShadow": props(show=lit(False)),
        }
        if self.tooltip_page:
            vco["visualTooltip"] = props(type=lit("ReportPage"), section=lit("tooltip"))
        vco.update(self.vco)
        visual["visualContainerObjects"] = vco
        if self.sync:
            visual["syncGroup"] = {"groupName": self.sync, "fieldChanges": True, "filterChanges": True}
        visual["drillFilterOtherVisuals"] = True
        out = {"$schema": VISUAL_SCHEMA, "name": self.name,
               "position": {"x": round(self.x, 1), "y": round(self.y, 1), "z": z,
                            "height": round(self.h, 1), "width": round(self.w, 1), "tabOrder": z},
               "visual": visual}
        if self.filters:
            out["filterConfig"] = {"filters": self.filters}
        return out


def inner(box, top=44, pad=10, bottom=8):
    x, y, w, h = box[:4]
    return x + pad, y + top, w - 2 * pad, h - top - bottom


AXIS_FONT = dict(fontSize=lit(9), labelColor=color(MUTED), fontFamily=lit(FONT))


def axes(cat_show=True, val_show=True, continuous=False, val_fmt_pct=False):
    o = {
        "categoryAxis": props(show=lit(cat_show), showAxisTitle=lit(False), gridlineShow=lit(False),
                              **({"axisType": lit("Scalar")} if continuous else {"axisType": lit("Categorical")}),
                              **AXIS_FONT),
        "valueAxis": props(show=lit(val_show), showAxisTitle=lit(False), gridlineShow=lit(val_show),
                           gridlineColor=color("#EEF1F6"), gridlineStyle=lit("dotted"), **AXIS_FONT),
        "legend": props(show=lit(False)),
    }
    return o


def labels(show=True, size=9, c=INK, units=None, precision=None):
    p = dict(show=lit(show), fontSize=lit(size), color=color(c), fontFamily=lit(FONT))
    if units is not None:
        p["labelDisplayUnits"] = lit(units)
    if precision is not None:
        p["labelPrecision"] = {"expr": {"Literal": {"Value": f"{precision}L"}}}
    return {"labels": props(**p)}


def fill(c):
    return {"dataPoint": props(fill=color(c))}


def fill_measure(name):
    return {"dataPoint": [{"properties": {"fill": measure_color(name)}, "selector": ALL_POINTS}]}


# ---- building blocks


def slicers(p):
    out = []
    for k, (ent, prop, sync) in enumerate([("Dates", "year", "year"), ("Markets", "market_label", "market"),
                                           ("Sales", "segment", "segment")]):
        x = 760 + k * 172
        out.append(V(f"{p}_slicer_{sync}", "slicer", x + 2, 25, 160, 32,
                     roles={"Values": [proj(col(ent, prop), None, True)]},
                     sort=[(col(ent, prop), "Ascending")],
                     objects={"data": props(mode=lit("Dropdown")),
                              "header": props(show=lit(False)),
                              "items": props(fontSize=lit(10), fontColor=color(INK), fontFamily=lit(FONT),
                                             background=color("#FFFFFF")),
                              "selection": props(selectAllCheckboxEnabled=lit(True))},
                     sync=sync))
    return out


def nav_buttons(p):
    out = []
    for k, (key, label, _icon) in enumerate(NAV):
        if key == p:
            continue
        out.append(V(f"{p}_nav_{key}", "actionButton", 12, 110 + k * 46, 176, 40,
                     objects={"icon": props(show=lit(False)), "outline": props(show=lit(False)),
                              "fill": [{"properties": {"show": lit(False)}},
                                       {"properties": {"show": lit(True), "fillColor": color("#FFFFFF"),
                                                       "transparency": lit(88)},
                                        "selector": {"id": "hover"}}],
                              "text": props(show=lit(False))},
                     vco={"visualLink": props(show=lit(True), type=lit("PageNavigation"),
                                              navigationSection=lit(key))}))
    return out


def kpi_row(p, specs, sparkline=True):
    out = []
    accents = [INDIGO, TEAL, VIOLET, CORAL, AMBER]
    for k, ((x, y, w, h), (mname, disp)) in enumerate(zip(tiles(len(specs)), specs)):
        out.append(V(f"{p}_kpi_{k}", "card", x + 8, y + 24, w - 16, 42,
                     roles={"Values": [proj(mea(mname), disp)]},
                     objects={"labels": props(color=color(INK), fontSize=lit(22), fontFamily=lit(FONT_SB),
                                              labelDisplayUnits=lit(0),
                                              **({"labelPrecision": {"expr": {"Literal": {"Value": "1L"}}}}
                                                 if mname in MONEY_MEASURES else {})),
                              "categoryLabels": props(show=lit(False)),
                              "wordWrap": props(show=lit(False))}))
        if sparkline:
            out.append(V(f"{p}_spark_{k}", "areaChart", x + 6, y + 64, w - 12, 54,
                         roles={"Category": [proj(col("Dates", "month_start"), "Month", True)],
                                "Y": [proj(mea(mname), disp)]},
                         sort=[(col("Dates", "month_start"), "Ascending")],
                         objects={**axes(False, False, continuous=True),
                                  **fill(accents[k % 5]),
                                  "lineStyles": props(strokeWidth=lit(2), showMarker=lit(False)),
                                  "labels": props(show=lit(False)),
                                  "general": props(responsive=lit(False))}))
    return out


def bar(name, box, cat, measure_name, disp, c=INDIGO, sort_measure=True, color_measure=None, pct=False,
        tooltip=False, top=44, filters=None, sort=None):
    x, y, w, h = inner(box, top=top)
    obj = {**axes(True, False), **labels(True, 9, INK),
           "valueAxis": props(show=lit(False), gridlineShow=lit(False)),
           "categoryAxis": props(show=lit(True), showAxisTitle=lit(False), fontSize=lit(10),
                                 labelColor=color(INK), fontFamily=lit(FONT), maxMarginFactor=lit(35))}
    obj.update(fill_measure(color_measure) if color_measure else fill(c))
    return V(name, "clusteredBarChart", x, y, w, h,
             roles={"Category": [proj(cat, None, True)], "Y": [proj(mea(measure_name), disp)]},
             sort=sort or ([(mea(measure_name), "Descending")] if sort_measure else []),
             objects=obj, tooltip_page=tooltip, filters=filters or [])


def exclude_blank(fname, entity, prop):
    return {"name": fname, "field": col(entity, prop), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "f", "Entity": entity, "Type": 0}],
                       "Where": [{"Condition": {"Not": {"Expression": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                                       "Property": prop}}],
                           "Values": [[{"Literal": {"Value": "null"}}]]}}}}}]}}


def panel(p, key):
    return PAGES[p]["panels"][key]




def column_chart(name, box, cat, measure_name, disp, c=INDIGO, color_measure=None, sort_desc=True, top=46,
                 label_size=8, sort=None):
    x, y, w, h = inner(box, top=top)
    obj = {**axes(True, False), **labels(True, label_size, INK)}
    obj["categoryAxis"] = props(show=lit(True), showAxisTitle=lit(False), fontSize=lit(8), labelColor=color(MUTED),
                                fontFamily=lit(FONT), axisType=lit("Categorical"))
    obj.update(fill_measure(color_measure) if color_measure else fill(c))
    return V(name, "clusteredColumnChart", x, y, w, h,
             roles={"Category": [proj(cat, None, True)], "Y": [proj(mea(measure_name), disp)]},
             sort=sort or ([(mea(measure_name), "Descending")] if sort_desc else []), objects=obj)


def donut(name, box, cat, measure_name, disp, top=46):
    x, y, w, h = inner(box, top=top)
    return V(name, "donutChart", x, y, w, h,
             roles={"Category": [proj(cat, None, True)], "Y": [proj(mea(measure_name), disp)]},
             sort=[(mea(measure_name), "Descending")],
             objects={"legend": props(show=lit(True), position=lit("Right"), fontSize=lit(9), labelColor=color(INK), showTitle=lit(False)),
                      "labels": props(show=lit(True), labelStyle=lit("Percent of total"), fontSize=lit(9),
                                      color=color(INK)),
                      "slices": props(innerRadiusRatio=lit(64))})


def table(name, box, projections, sort, widths, color_cols=(), top=48, tooltip=False, row_pad=6, text=10):
    x, y, w, h = inner(box, top=top, pad=12)
    values = [{"properties": {"fontColorPrimary": color(INK), "backColorPrimary": color("#FFFFFF"),
                              "backColorSecondary": color("#FAFBFD"), "fontSize": lit(text),
                              "wordWrap": lit(False)}}]
    for measure_name, color_measure in color_cols:
        values.append({"properties": {"backColor": measure_color(color_measure), "fontColor": color("#FFFFFF")},
                       "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                    "metadata": f"{M}.{measure_name}"}})
    return V(name, "tableEx", x, y, w, h, roles={"Values": projections}, sort=sort,
             objects={"grid": props(gridVertical=lit(False), gridHorizontal=lit(True),
                                    gridHorizontalColor=color("#EEF1F6"), rowPadding=lit(row_pad),
                                    textSize=lit(text), outlineColor=color("#FFFFFF")),
                      "columnHeaders": props(fontColor=color(MUTED), backColor=color("#FFFFFF"), fontSize=lit(9),
                                             fontFamily=lit(FONT_SB), wordWrap=lit(True)),
                      "values": values, "total": props(totals=lit(False)),
                      "columnWidth": [{"properties": {"value": lit(wd)}, "selector": {"metadata": qr}}
                                      for qr, wd in widths.items()]},
             tooltip_page=tooltip)


def tolerance_slicer(p, box):
    lab = V(f"{p}_tolerance_label", "textbox", box[0] + box[2] - 262, box[1] + 12, 130, 28,
            objects={"general": [{"properties": {"paragraphs": [{"textRuns": [
                {"value": "Tolerance (days late)", "textStyle": {"fontSize": "9pt", "color": MUTED}}],
                "horizontalTextAlignment": "right"}]}}]})
    sl = V(f"{p}_tolerance", "slicer", box[0] + box[2] - 126, box[1] + 10, 112, 32,
           roles={"Values": [proj(col("Delay Tolerance", "Delay Tolerance"), "Tolerance (days)", True)]},
           sort=[(col("Delay Tolerance", "Delay Tolerance"), "Ascending")],
           objects={"data": props(mode=lit("Dropdown")),
                    "header": props(show=lit(False)),
                    "selection": props(singleSelect=lit(True), strictSingleSelect=lit(True)),
                    "items": props(fontSize=lit(10), fontColor=color(INK), background=color("#FFFFFF"))},
           vco={"border": props(show=lit(True), color=color(LINE), radius=lit(8))})
    return [lab, sl]


def overview():
    p = "overview"
    v = slicers(p) + nav_buttons(p)
    v += kpi_row(p, [("Revenue", "Revenue"), ("Profit", "Profit"), ("Profit Margin", "Profit margin"),
                     ("Orders", "Orders"), ("Late Rate", "Late deliveries")])
    x, y, w, h = inner(panel(p, "map"), top=48, pad=8)
    v.append(V(f"{p}_map", "azureMap", x, y, w, h,
               roles={"Category": [proj(col("Geography", "country"), "Country", True)],
                      "Size": [proj(mea("Revenue"), "Revenue")]},
               objects={"bubbleLayer": props(bubbleColor=color(INDIGO), bubbleRadius=lit(4),
                                             minBubbleRadius={"expr": {"Literal": {"Value": "3L"}}},
                                             maxRadius={"expr": {"Literal": {"Value": "18L"}}},
                                             bubbleTransparency=lit(25)),
                        "mapStyles": props(mapStyle=lit("grayscale_light")),
                        "mapControls": props(autoZoom=lit(True), showZoomButtons=lit(False),
                                             showStylePicker=lit(False))},
               tooltip_page=True))
    v.append(bar(f"{p}_market", panel(p, "market"), col("Markets", "market_label"), "Revenue", "Revenue", c=INDIGO))
    x, y, w, h = inner(panel(p, "insights"), top=44, pad=10, bottom=6)
    items = [("Insight Delivery", "DELIVERY"), ("Insight Margin", "MARGIN LEAK"), ("Insight Fraud", "SUSPECTED FRAUD")]
    hh = h / 3
    for k, (m, lab) in enumerate(items):
        v.append(V(f"{p}_insight_{k}", "card", x, y + k * hh, w, hh - 4,
                   roles={"Values": [proj(mea(m), lab)]},
                   objects={"labels": props(color=color(INK), fontSize=lit(10), fontFamily=lit(FONT)),
                            "wordWrap": props(show=lit(True)),
                            "categoryLabels": props(show=lit(True), color=color(INDIGO), fontSize=lit(8),
                                                    fontFamily=lit(FONT_SB))},
                   vco={"background": props(show=lit(True), color=color("#F5F7FC"), transparency=lit(0)),
                        "border": props(show=lit(True), color=color("#E6EAF2"), radius=lit(8))}))
    return v


def delivery():
    p = "delivery"
    v = slicers(p) + nav_buttons(p)
    v += kpi_row(p, [("Late Rate", "Late deliveries"), ("On Time Within Tolerance", "On time within tolerance"),
                     ("Avg Delay Late", "Average delay of late orders"),
                     ("Revenue Delivered Late", "Revenue delivered late"), ("Cancelled Orders", "Cancelled shipments")])
    box = panel(p, "modes")
    v += tolerance_slicer(p, box)
    projections = [proj(col("ShippingModes", "shipping_mode"), "Shipping mode"),
                   proj(mea("Avg Days Scheduled"), "Days promised"), proj(mea("Avg Days Real"), "Days taken"),
                   proj(mea("Late Rate"), "Late"), proj(mea("On Time Within Tolerance"), "On time (with tolerance)"),
                   proj(mea("Shipped Orders"), "Shipped orders"), proj(mea("Revenue"), "Revenue")]
    widths = {"ShippingModes.shipping_mode": 118, f"{M}.Avg Days Scheduled": 70, f"{M}.Avg Days Real": 66,
              f"{M}.Late Rate": 64, f"{M}.On Time Within Tolerance": 92, f"{M}.Shipped Orders": 72, f"{M}.Revenue": 96}
    v.append(table(f"{p}_modes", box, projections, [(col("ShippingModes", "shipping_mode"), "Ascending")], widths,
                   color_cols=[("Late Rate", "Late Color")], row_pad=7, text=11))
    v.append(bar(f"{p}_mode_bar", panel(p, "mode_bar"), col("ShippingModes", "shipping_mode"), "Late Rate",
                 "Late deliveries", color_measure="Late Color"))
    v.append(column_chart(f"{p}_region", panel(p, "region"), col("Geography", "region"), "Late Rate",
                          "Late deliveries", color_measure="Late Color", label_size=7))
    v.append(donut(f"{p}_status", panel(p, "status"), col("Sales", "delivery_status"), "Orders", "Orders"))
    return v


def profit():
    p = "profit"
    v = slicers(p) + nav_buttons(p)
    v += kpi_row(p, [("Gross Sales", "Gross sales"), ("Discounts", "Discounts"), ("Revenue", "Revenue"),
                     ("Profit", "Profit"), ("Loss Lines %", "Loss-making lines")])
    x, y, w, h = inner(panel(p, "dept"), top=48)
    v.append(V(f"{p}_dept", "waterfallChart", x, y, w, h,
               roles={"Category": [proj(col("Products", "department"), "Department", True)],
                      "Y": [proj(mea("Profit"), "Profit")]},
               sort=[(mea("Profit"), "Descending")],
               objects={**axes(True, True), **labels(True, 8, INK),
                        "sentimentColors": props(increaseFill=color(TEAL), decreaseFill=color(CORAL),
                                                 totalFill=color(INDIGO))}))
    v.append(bar(f"{p}_loss", panel(p, "loss"), col("Products", "department"), "Loss Amount", "Losses",
                 c=CORAL))
    projections = [proj(col("Products", "product"), "Product"), proj(col("Products", "category"), "Category"),
                   proj(mea("Revenue"), "Revenue"), proj(mea("Profit"), "Profit"),
                   proj(mea("Profit Margin"), "Margin"), proj(mea("Discount Rate"), "Discount"),
                   proj(mea("Loss Lines %"), "Lines at a loss")]
    widths = {"Products.product": 160, "Products.category": 96, f"{M}.Revenue": 84, f"{M}.Profit": 76,
              f"{M}.Profit Margin": 58, f"{M}.Discount Rate": 58, f"{M}.Loss Lines %": 66}
    v.append(table(f"{p}_products", panel(p, "products"), projections, [(mea("Revenue"), "Descending")], widths,
                   color_cols=[("Profit Margin", "Margin Color")]))
    x, y, w, h = inner(panel(p, "discount"), top=48)
    v.append(V(f"{p}_discount", "scatterChart", x, y, w, h,
               roles={"Category": [proj(col("Products", "category"), "Category", True)],
                      "X": [proj(mea("Discount Rate"), "Discount rate")],
                      "Y": [proj(mea("Profit Margin"), "Profit margin")],
                      "Size": [proj(mea("Revenue"), "Revenue")]},
               objects={"categoryAxis": props(show=lit(True), showAxisTitle=lit(True), titleText=lit("Discount rate"),
                                              gridlineShow=lit(True), gridlineColor=color("#EEF1F6"), **AXIS_FONT,
                                              titleColor=color(MUTED), titleFontSize=lit(9)),
                        "valueAxis": props(show=lit(True), showAxisTitle=lit(True), titleText=lit("Profit margin"),
                                           gridlineShow=lit(True), gridlineColor=color("#EEF1F6"), **AXIS_FONT,
                                           titleColor=color(MUTED), titleFontSize=lit(9)),
                        "legend": props(show=lit(False)), **fill_measure("Margin Color")}))
    return v


def markets():
    p = "markets"
    v = slicers(p) + nav_buttons(p)
    v += kpi_row(p, [("Customers", "Customers"), ("Avg Order Value", "Average order value"),
                     ("Items per Order", "Items per order"), ("Revenue per Customer", "Revenue per customer"),
                     ("Profit Margin", "Profit margin")])
    x, y, w, h = inner(panel(p, "heat"), top=48, pad=12)
    v.append(V(f"{p}_heat", "pivotTable", x, y, w, h,
               roles={"Rows": [proj(col("Markets", "market_label"), "Market", True)],
                      "Columns": [proj(col("Sales", "segment"), "Segment", True)],
                      "Values": [proj(mea("Profit Margin"), "Profit margin")]},
               objects={"values": [{"properties": {"backColor": measure_color("Margin Heat Color"),
                                                   "fontColor": measure_color("Margin Heat Font")},
                                    "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}],
                                                 "metadata": f"{M}.Profit Margin"}},
                                   {"properties": {"fontSize": lit(11)}}],
                        "grid": props(rowPadding=lit(4), gridVertical=lit(True), gridVerticalColor=color("#FFFFFF"),
                                      gridHorizontal=lit(True), gridHorizontalColor=color("#FFFFFF"),
                                      gridVerticalWeight=lit(2), gridHorizontalWeight=lit(2)),
                        "columnHeaders": props(fontColor=color(MUTED), fontSize=lit(9), fontFamily=lit(FONT_SB),
                                               alignment=lit("Center")),
                        "rowHeaders": props(fontColor=color(INK), fontSize=lit(10), fontFamily=lit(FONT_SB)),
                        "subTotals": props(rowSubtotals=lit(False), columnSubtotals=lit(False)),
                        "total": props(totals=lit(False))}))
    v.append(donut(f"{p}_segment", panel(p, "segment"), col("Sales", "segment"), "Revenue", "Revenue"))
    projections = [proj(col("Geography", "country"), "Country"), proj(col("Markets", "market_label"), "Market"),
                   proj(mea("Revenue"), "Revenue"), proj(mea("Profit Margin"), "Margin"), proj(mea("Orders"), "Orders"),
                   proj(mea("Avg Order Value"), "Avg order"), proj(mea("Late Rate"), "Late"),
                   proj(mea("Fraud Rate"), "Fraud")]
    widths = {"Geography.country": 200, "Markets.market_label": 140, f"{M}.Revenue": 110, f"{M}.Profit Margin": 100,
              f"{M}.Orders": 100, f"{M}.Avg Order Value": 100, f"{M}.Late Rate": 100, f"{M}.Fraud Rate": 100}
    v.append(table(f"{p}_countries", panel(p, "countries"), projections, [(mea("Revenue"), "Descending")], widths,
                   color_cols=[("Profit Margin", "Margin Color"), ("Late Rate", "Late Color")], tooltip=True))
    return v


NOTES = [
    ("Source", "DataCo Smart Supply Chain for Big Data Analysis (Constante, Silva & Pereira, Mendeley Data, CC BY 4.0), also published on Kaggle."),
    ("Scope", "January 2015 to September 2017. Later orders are left out: the catalogue falls from about 50 products to under 20 and orders shrink to a single line."),
    ("Markets", "Each market is recorded over its own periods in the source, so markets are compared over the whole period, not month by month."),
    ("Definitions", "Revenue is net of discounts. A late order arrives after its scheduled date; cancelled shipments are left out of delivery rates."),
    ("Privacy", "Customer names, e-mails and addresses are not loaded."),
]


def risk():
    p = "risk"
    v = slicers(p) + nav_buttons(p)
    v += kpi_row(p, [("Fraud Orders", "Suspected fraud orders"), ("Fraud Revenue", "Revenue under fraud review"),
                     ("Fraud Rate Transfers", "Fraud rate on transfers"), ("Cancelled Revenue", "Cancelled revenue")])
    v.append(bar(f"{p}_pay", panel(p, "pay"), col("Sales", "payment_type"), "Fraud Rate", "Suspected fraud rate",
                 c=CORAL))
    v.append(column_chart(f"{p}_fraud_region", panel(p, "fraud_region"), col("Geography", "region"), "Fraud Rate",
                          "Suspected fraud rate", c=CORAL, label_size=7))
    v.append(bar(f"{p}_fraud_countries", panel(p, "fraud_countries"), col("Geography", "country"), "Fraud Orders",
                 "Orders flagged", c=VIOLET, tooltip=True))
    bx = panel(p, "notes")
    paragraphs = []
    for head, body in NOTES:
        paragraphs.append({"textRuns": [{"value": head + " · ", "textStyle": {"fontSize": "9pt", "color": INK,
                                                                              "fontWeight": "bold"}},
                                        {"value": body, "textStyle": {"fontSize": "9pt", "color": MUTED}}]})
    v.append(V(f"{p}_notes", "textbox", bx[0] + 12, bx[1] + 46, bx[2] - 24, bx[3] - 52,
               objects={"general": [{"properties": {"paragraphs": paragraphs}}]}))
    return v


def profile():
    p = "profile"
    v = nav_buttons(p)
    v.append(V(f"{p}_name", "card", X0 - 4, 6, 380, 44,
               roles={"Values": [proj(mea("Selected Country"), "Country")]},
               objects={"labels": props(color=color(INK), fontSize=lit(22), fontFamily=lit(FONT_SB)),
                        "categoryLabels": props(show=lit(False)), "general": props(alignment=lit("left"))}))
    v.append(V(f"{p}_back", "actionButton", X1 - 120, 24, 120, 34,
               objects={"icon": [{"properties": {"show": lit(False), "shapeType": lit("back"), "lineColor": color(INK),
                                                 "iconPlacement": lit("left"), "iconSize": lit(14)},
                                  "selector": {"id": "default"}}],
                        "text": [{"properties": {"show": lit(True), "text": lit("←  Back"), "fontColor": color(INK),
                                                 "fontSize": lit(10)}, "selector": {"id": "default"}}],
                        "outline": props(show=lit(False)), "fill": props(show=lit(False))},
               vco={"visualLink": props(show=lit(True), type=lit("Back"))}))
    v += kpi_row(p, [("Revenue", "Revenue"), ("Profit Margin", "Profit margin"), ("Orders", "Orders"),
                     ("Late Rate", "Late deliveries"), ("Fraud Rate", "Suspected fraud rate")])
    x, y, w, h = inner(panel(p, "p_trend"), top=48)
    v.append(V(f"{p}_trend", "areaChart", x, y, w, h,
               roles={"Category": [proj(col("Dates", "month_start"), "Month", True)],
                      "Y": [proj(mea("Revenue"), "Revenue")]},
               sort=[(col("Dates", "month_start"), "Ascending")],
               objects={**axes(True, True, continuous=True), **fill(INDIGO),
                        "lineStyles": props(strokeWidth=lit(2), showMarker=lit(False))}))
    v.append(bar(f"{p}_mode", panel(p, "p_mode"), col("ShippingModes", "shipping_mode"), "Late Rate",
                 "Late deliveries", color_measure="Late Color", sort=[(col("ShippingModes", "shipping_mode"), "Ascending")]))
    v.append(bar(f"{p}_dept", panel(p, "p_dept"), col("Products", "department"), "Revenue", "Revenue"))
    v.append(donut(f"{p}_seg", panel(p, "p_seg"), col("Sales", "segment"), "Revenue", "Revenue"))
    return v


def tooltip_page():
    p = "tooltip"
    v = [V(f"{p}_name", "card", 10, 8, 300, 40,
           roles={"Values": [proj(mea("Selected Country"), "Country")]},
           objects={"labels": props(color=color("#FFFFFF"), fontSize=lit(16), fontFamily=lit(FONT_SB)),
                    "categoryLabels": props(show=lit(False))})]
    items = [("Revenue", "Revenue"), ("Profit Margin", "Margin"), ("Late Rate", "Late deliveries"),
             ("Fraud Rate", "Suspected fraud")]
    for k, (m, disp) in enumerate(items):
        cx = 18 + (k % 2) * 146
        cy = 60 + (k // 2) * 64
        v.append(V(f"{p}_kpi_{k}", "card", cx, cy, 138, 58, roles={"Values": [proj(mea(m), disp)]},
                   objects={"labels": props(color=color(INK), fontSize=lit(16), fontFamily=lit(FONT_SB)),
                            "categoryLabels": props(show=lit(True), color=color(MUTED), fontSize=lit(9))}))
    return v


PAGES_BUILD = [
    ("overview", "Overview", overview, None),
    ("delivery", "Delivery", delivery, None),
    ("profit", "Profitability", profit, None),
    ("markets", "Markets & customers", markets, None),
    ("risk", "Risk & fraud", risk, None),
    ("profile", "Country profile", profile, "drill"),
    ("tooltip", "Country tooltip", tooltip_page, "tooltip"),
]



def page_objects(img):
    return {"background": [{"properties": {
                "image": {"image": {"name": lit(img),
                                    "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources",
                                                                             "PackageType": 1, "ItemName": img}}},
                                    "scaling": lit("Fit")}},
                "transparency": lit(0)}}],
            "outspace": [{"properties": {"color": color(BG)}}]}


THEME = {
    "name": "Global Supply Chain Cockpit",
    "dataColors": [INDIGO, TEAL, AMBER, CORAL, VIOLET, SKY, "#0B1F44", "#9AA4B2"],
    "foreground": INK, "foregroundNeutralSecondary": MUTED, "foregroundNeutralTertiary": "#9AA4B2",
    "background": "#FFFFFF", "backgroundLight": "#F7F9FC", "backgroundNeutral": "#E6EAF2",
    "tableAccent": INDIGO, "good": TEAL, "neutral": AMBER, "bad": CORAL,
    "maximum": INDIGO, "center": "#C7CCF4", "minimum": "#EEF0FB",
    "textClasses": {
        "callout": {"fontSize": 22, "fontFace": FONT_SB, "color": INK},
        "title": {"fontSize": 12, "fontFace": FONT_SB, "color": INK},
        "header": {"fontSize": 11, "fontFace": FONT_SB, "color": INK},
        "label": {"fontSize": 10, "fontFace": FONT, "color": MUTED},
    },
    "visualStyles": {"*": {"*": {
        "background": [{"show": False}], "border": [{"show": False}], "dropShadow": [{"show": False}],
        "visualHeader": [{"show": False}], "title": [{"show": False}],
        "visualTooltip": [{"titleFontColor": INK, "valueFontColor": INK, "background": "#FFFFFF"}],
    }}},
}


def write_report():
    item = OUT / f"{NAME}.Report"
    de = item / "definition"
    (de / "pages").mkdir(parents=True)
    wjson(item / "definition.pbir", {"$schema": f"{SCHEMAS}/item/report/definitionProperties/1.0.0/schema.json",
                                     "version": "4.0",
                                     "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    wjson(de / "version.json", {"$schema": f"{SCHEMAS}/item/report/definition/versionMetadata/1.0.0/schema.json",
                                "version": "2.0.0"})
    versions = {"visual": "2.2.0", "page": "2.0.0", "report": "3.0.0"}
    images = [f"bg_{n}.png" for n in PAGES] + ["bg_tooltip.png"]
    wjson(de / "report.json", {
        "$schema": REPORT_SCHEMA,
        "themeCollection": {
            "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": versions, "type": "SharedResources"},
            "customTheme": {"name": THEME_FILE, "reportVersionAtImport": versions, "type": "RegisteredResources"}},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}]
             + [{"name": im, "path": im, "type": "Image"} for im in images]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True}})
    wjson(de / "pages" / "pages.json", {
        "$schema": f"{SCHEMAS}/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [n for n, *_ in PAGES_BUILD], "activePageName": "overview"})
    for name, display, build, kind in PAGES_BUILD:
        folder = de / "pages" / name
        page = {"$schema": PAGE_SCHEMA, "name": name, "displayName": display}
        if kind == "tooltip":
            page.update({"displayOption": "ActualSize", "height": 200, "width": 320,
                         "objects": page_objects("bg_tooltip.png"),
                         "pageBinding": {"name": "tooltip_binding", "type": "Tooltip", "parameters": []},
                         "type": "Tooltip", "visibility": "HiddenInViewMode"})
        else:
            page.update({"displayOption": "FitToPage", "height": H, "width": W,
                         "objects": page_objects(f"bg_{name}.png")})
        if kind == "drill":
            page["pageBinding"] = {"name": "profile_binding", "type": "Drillthrough",
                                   "parameters": [{"name": "profile_country", "boundFilter": "dt_country",
                                                   "fieldExpr": col("Geography", "country")}]}
            page["filterConfig"] = {"filters": [{"name": "dt_country", "field": col("Geography", "country"),
                                                 "type": "Categorical", "howCreated": "Drillthrough"}]}
            page["type"] = "Drillthrough"
            page["visibility"] = "HiddenInViewMode"
        wjson(folder / "page.json", page)
        for z, vis in enumerate(build()):
            wjson(folder / "visuals" / vis.name / "visual.json", vis.to_json(z * 1000))
    res = item / "StaticResources"
    (res / "SharedResources" / "BaseThemes").mkdir(parents=True)
    shutil.copyfile(BASE_THEME_SRC, res / "SharedResources" / "BaseThemes" / f"{BASE_THEME}.json")
    reg = res / "RegisteredResources"
    wjson(reg / THEME_FILE, THEME)
    for im in images:
        shutil.copyfile(BG_DIR / im, reg / im)


def wjson(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def wtext(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip("\n") + "\n", encoding="utf-8")


def main():
    global DEFAULT_FOLDER
    import argparse
    ap = argparse.ArgumentParser(description="Write the PBIP project to powerbi/")
    ap.add_argument("--data-folder", default=DEFAULT_FOLDER,
                    help="absolute Windows path of the data/ folder, stored in the DataFolder parameter")
    DEFAULT_FOLDER = ap.parse_args().data_folder.rstrip("\\")
    for it in (f"{NAME}.SemanticModel", f"{NAME}.Report"):
        shutil.rmtree(OUT / it, ignore_errors=True)
    write_model()
    write_report()
    wjson(OUT / f"{NAME}.pbip", {"$schema": f"{SCHEMAS}/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0",
                                 "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                 "settings": {"enableAutoRecovery": True}})
    wtext(OUT / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print("written", OUT)


if __name__ == "__main__":
    main()
