"""Shared layout: backgrounds and visuals use the same boxes."""
W, H = 1280, 720
RAIL = 200
X0, X1 = 216, 1264
NAVY, NAVY2 = "#060B1A", "#0A1330"
INK, MUTED, LINE, BG, CARD = "#E9EEFC", "#8C9AC0", "#1F2C4D", "#050A18", "#0E1830"
CARD2, GRID = "#111E3B", "#1C294A"
INDIGO, TEAL, AMBER, CORAL, SKY, VIOLET = "#7B8CFF", "#22E1C3", "#FFB547", "#FF5C7A", "#38C8FF", "#B57BFF"
BRAND1, BRAND2 = "SUPPLY CHAIN", "GLOBAL COCKPIT"
SLICER_LABELS = ["YEAR", "MARKET", "CUSTOMER SEGMENT"]
HINT = "<b>Tip</b> · right-click a country, then <b>Drill through</b>, to open its profile. Hover a country for its quick card."
FOOT = "<b>Data</b> · DataCo Smart Supply Chain (Kaggle / Mendeley Data, CC BY 4.0), 171,962 order lines, Jan 2015 – Sep 2017<br><b>Design & build</b> · Thierry Daconceição Alvares"
NAV = [("overview", "Overview", "globe"), ("delivery", "Delivery", "truck"), ("profit", "Profitability", "coins"),
       ("markets", "Markets & customers", "users"), ("risk", "Risk & fraud", "shield")]


def tiles(n, y=76, h=120):
    w = (X1 - X0 - 12 * (n - 1)) / n
    return [(X0 + i * (w + 12), y, w, h) for i in range(n)]


PAGES = {
 "overview": dict(title="Global supply chain cockpit", sub="DataCo · 57,349 orders · 164 countries · 5 markets · January 2015 – September 2017",
   kpis=["Revenue", "Profit", "Profit margin", "Orders", "Late deliveries"],
   panels={"map": (216, 208, 632, 496, "Revenue by country", "Bubble size = revenue · hover for the country card"),
           "market": (860, 208, 404, 244, "Revenue by market", "Net of discounts"),
           "insights": (860, 464, 404, 240, "What the data says", "Computed live from the current filters")}),
 "delivery": dict(title="Delivery performance", sub="Promise versus reality: scheduled and actual shipping days, by shipping mode and region",
   kpis=["Late deliveries", "On time · tolerance", "Avg delay (late)", "Revenue shipped late", "Cancelled orders"],
   panels={"modes": (216, 208, 632, 244, "Promise vs reality by shipping mode", "Days promised, days taken, share delivered late"),
           "mode_bar": (860, 208, 404, 244, "Late deliveries by shipping mode", "Share of shipped orders delivered late"),
           "region": (216, 464, 632, 240, "Late deliveries by region", "Share of shipped orders delivered late"),
           "status": (860, 464, 404, 240, "Delivery outcome", "Orders by delivery status")}),
 "profit": dict(title="Profitability", sub="Where the margin is made, and where discounts and loss-making lines give it away",
   kpis=["Gross sales", "Discounts", "Revenue", "Profit", "Loss-making lines"],
   panels={"dept": (216, 208, 632, 244, "Profit by department", "Each bar adds to total profit"),
           "loss": (860, 208, 404, 244, "Losses from lines sold below cost", "By department, loss from lines sold at a loss"),
           "products": (216, 464, 632, 240, "Top products", "Ranked by revenue"),
           "discount": (860, 464, 404, 240, "Discount rate vs profit margin", "One bubble per category · size = revenue")}),
 "markets": dict(title="Markets and customers", sub="Who buys, where, and how profitably",
   kpis=["Customers", "Avg order value", "Items per order", "Revenue / customer", "Profit margin"],
   panels={"heat": (216, 208, 632, 244, "Profit margin: market × customer segment", "Darker = higher margin"),
           "segment": (860, 208, 404, 244, "Revenue by customer segment", "Net of discounts"),
           "countries": (216, 464, 1048, 240, "Top countries", "Right-click a country, then Drill through, to open its profile")}),
 "risk": dict(title="Risk and fraud", sub="Suspected fraud, cancelled shipments, and how far the data can be trusted",
   kpis=["Suspected fraud orders", "Revenue under review", "Fraud rate · transfers", "Cancelled revenue"],
   panels={"pay": (216, 208, 516, 244, "Suspected fraud by payment type", "Share of orders flagged"),
           "fraud_region": (744, 208, 520, 244, "Suspected fraud rate by region", "Share of orders flagged"),
           "fraud_countries": (216, 464, 516, 240, "Countries with the most suspected fraud", "Orders flagged"),
           "notes": (744, 464, 520, 240, "About the data", "Scope and choices behind every number")}),
 "profile": dict(title="", sub="Country profile · opened by drill through",
   kpis=["Revenue", "Profit margin", "Orders", "Late deliveries", "Fraud rate"],
   panels={"p_trend": (216, 208, 632, 244, "Monthly revenue", "Selected country"),
           "p_mode": (860, 208, 404, 244, "Late deliveries by shipping mode", "Selected country"),
           "p_dept": (216, 464, 632, 240, "Revenue by department", "Selected country"),
           "p_seg": (860, 464, 404, 240, "Revenue by customer segment", "Selected country")}),
}
