def main(doc, method):
	if doc.is_stock_item:
		doc.valuation_method = 'Moving Average'
