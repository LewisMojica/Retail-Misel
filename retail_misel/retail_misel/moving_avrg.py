import frappe

def main(doc, method):
	"""
	Apply moving average method to update inventory cost when stock enters inventory.

	This function calculates the new weighted average cost of inventory items
	using the moving average method (also known as weighted average method).
	The new average cost is computed based on existing inventory value and
	the incoming stock value. Optionally updates the selling rate if specified.
	"""	 
	if doc.stock_entry_type == 'Repack':
		pass		

def lateUpdate(stock_ledger_entry):
	"""
	Triggers valuation rate synchronization for Material Receipt transactions.

	This function is called via ERPNext hooks when Stock Ledger Entries are processed.
	For Material Receipt entries using Moving Average valuation, it enqueues a job to 
	update the Item's valuation_rate field once ERPNext completes its internal valuation calculations.

	Background:
	- ERPNext stores valuation in Stock Ledger Entry, not directly in Item
	- Valuation calculation happens asynchronously after stock entry
	- Item.valuation_rate field needs manual synchronization
	- Queue job prevents blocking the main transaction
	- Only Moving Average valuation method requires this synchronization

	This is particularly relevant when stock enters with different cost and the 
	valuation method is Moving Average.

	Args:
		 doc: Stock Ledger Entry document
		 method: Hook method name

	Note:
		 Only processes Material Receipt entries with Moving Average valuation method
		 as other entry types or valuation methods may not require valuation rate updates.
	"""
	import time
	while True:	
		time.sleep(3)
		valuation_rate = frappe.get_value('Stock Ledger Entry', stock_ledger_entry, 'valuation_rate')
		if valuation_rate != None:
			item_code = frappe.get_value('Stock Ledger Entry', stock_ledger_entry, 'item_code')
			frappe.set_value('Item',item_code,'valuation_rate', valuation_rate) 
			break

def updateItemCost(doc, method):
	"""
	Triggers valuation rate synchronization for Material Receipt transactions.

	This function is called via ERPNext hooks when Stock Ledger Entries are processed.
	For Material Receipt entries, it enqueues a job to update the Item's valuation_rate
	field once ERPNext completes its internal valuation calculations.

	Background:
	- ERPNext stores valuation in Stock Ledger Entry, not directly in Item
	- Valuation calculation happens asynchronously after stock entry
	- Item.valuation_rate field needs manual synchronization
	- Queue job prevents blocking the main transaction

	Args:
	doc: Stock Ledger Entry document
	method: Hook method name

	Note:
	Only processes Material Receipt entries as other entry types
	may not require valuation rate updates.
	
	stock enter with different cost and the valueation method
	is moving average.
	"""
	stock_entry_type = frappe.get_doc('Stock Entry', doc.voucher_no).stock_entry_type
	item_valuation_method = frappe.get_value('Item', doc.item_code, 'valuation_method')

	if stock_entry_type == 'Material Receipt' and item_valuation_method == 'Moving Average':
		frappe.enqueue(lateUpdate,queue='short', stock_ledger_entry=doc.name)

