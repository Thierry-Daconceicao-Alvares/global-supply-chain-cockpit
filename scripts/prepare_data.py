"""DataCo Smart Supply Chain (Mendeley Data / Kaggle, CC BY 4.0) -> star schema in Parquet."""
import sys, pandas as pd, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from countries import ES_EN
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
d = pd.read_csv(ROOT / 'data' / 'raw' / 'DataCoSupplyChainDataset.csv', encoding='latin-1')
n_raw = len(d)
d['od'] = pd.to_datetime(d['order date (DateOrders)']); d['sd'] = pd.to_datetime(d['shipping date (DateOrders)'])
scope = (d.od >= '2015-01-01') & (d.od < '2017-10-01')
d = d[scope].copy()
miss = set(d['Order Country']) - set(ES_EN); assert not miss, miss
d['country'] = d['Order Country'].map(ES_EN)
d['region'] = d['Order Region'].str.replace(r'\s+', ' ', regex=True).str.strip()
d['region'] = d.region.replace({'West of USA': 'Western US', 'East of USA': 'Eastern US', 'US Center': 'Central US', 'South of USA': 'Southern US'})
geo = d.groupby('country').agg(market=('Market', lambda s: s.mode()[0]), region=('region', lambda s: s.mode()[0])).reset_index()
cancelled = d['Delivery Status'].eq('Shipping canceled')
f = pd.DataFrame({
 'order_item_id': d['Order Item Id'].astype('int64'), 'order_id': d['Order Id'].astype('int64'),
 'order_date': d.od.dt.normalize(), 'ship_date': d.sd.dt.normalize(),
 'customer_id': d['Order Customer Id'].astype('int64'), 'product_id': d['Product Card Id'].astype('int64'),
 'country': d.country, 'market': d.Market, 'region': d.region,
 'shipping_mode': d['Shipping Mode'], 'delivery_status': d['Delivery Status'],
 'order_status': d['Order Status'].str.replace('_', ' ').str.title(),
 'payment_type': d['Type'].str.title(), 'segment': d['Customer Segment'],
 'quantity': d['Order Item Quantity'].astype('int64'),
 'gross_sales': d['Sales'].round(2), 'discount': d['Order Item Discount'].round(2),
 'revenue': d['Order Item Total'].round(2), 'profit': d['Order Profit Per Order'].round(2),
 'days_real': d['Days for shipping (real)'].astype('int64'), 'days_scheduled': d['Days for shipment (scheduled)'].astype('int64'),
 'is_late': d['Late_delivery_risk'].astype('int64'), 'is_cancelled': cancelled.astype('int64'),
 'is_fraud': d['Order Status'].eq('SUSPECTED_FRAUD').astype('int64'),
})
f['delay_days'] = (f.days_real - f.days_scheduled).astype('int64')
f['is_loss'] = (f.profit < 0).astype('int64')
f['shipped'] = (1 - f.is_cancelled).astype('int64')
f.rename(columns={'gross_sales':'gross_sales_amt','discount':'discount_amt','revenue':'revenue_amt','profit':'profit_amt'}).to_parquet(OUT / 'sales.parquet', index=False)
geo.to_parquet(OUT / 'geography.parquet', index=False)
p = d.groupby('Product Card Id').agg(product=('Product Name', lambda s: s.iloc[0].strip()), category=('Category Name', lambda s: s.iloc[0].strip()),
    department=('Department Name', lambda s: s.iloc[0].strip()), list_price=('Product Price', 'max')).reset_index().rename(columns={'Product Card Id': 'product_id'})
p.to_parquet(OUT / 'products.parquet', index=False)
sm = pd.DataFrame({'shipping_mode': ['Same Day', 'First Class', 'Second Class', 'Standard Class'], 'mode_order': [1, 2, 3, 4], 'promised_days': [0, 1, 2, 4]})
sm.to_parquet(OUT / 'shipping_modes.parquet', index=False)
mk = pd.DataFrame({'market': ['Europe', 'LATAM', 'Pacific Asia', 'USCA', 'Africa'], 'market_label': ['Europe', 'Latin America', 'Asia-Pacific', 'US & Canada', 'Africa'], 'market_order': [1, 2, 3, 4, 5]})
mk.to_parquet(OUT / 'markets.parquet', index=False)
dt = pd.DataFrame({'date': pd.date_range('2015-01-01', '2017-09-30', freq='D')})
dt['year'] = dt.date.dt.year.astype('int64'); dt['quarter'] = 'Q' + dt.date.dt.quarter.astype(str)
dt['year_quarter'] = dt.year.astype(str) + ' ' + dt.quarter
dt['month_number'] = dt.date.dt.month.astype('int64'); dt['month'] = dt.date.dt.strftime('%b')
dt['month_start'] = dt.date.dt.to_period('M').dt.to_timestamp()
dt.to_parquet(OUT / 'dates.parquet', index=False)
print('raw', n_raw, 'kept', len(f), 'orders', f.order_id.nunique(), 'countries', f.country.nunique(), 'products', len(p))
print('geo market check', (d.groupby('country').Market.nunique() > 1).sum(), 'countries in >1 market')
s = f
print('revenue', s.revenue.sum(), 'profit', s.profit.sum(), 'margin', s.profit.sum() / s.revenue.sum())
o = s[s.shipped == 1].groupby('order_id').agg(late=('is_late', 'max'), delay=('delay_days', 'max'), mode=('shipping_mode', 'first'))
print('late orders', o.late.mean()); print(o.groupby('mode').late.mean())
print('fraud orders', s[s.is_fraud == 1].order_id.nunique(), s[s.is_fraud == 1].revenue.sum())
print('loss items', s.is_loss.mean(), s[s.is_loss == 1].profit.sum())
