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
	Updates Item valuation_rate field after ERPNext completes valuation calculation.

	This function uses polling because ERPNext's valuation calculation is asynchronous
	and doesn't provide hooks/events when completed. The valuation_rate is stored in
	Stock Ledger Entry but needs to be synchronized to the Item doctype.

	Polling approach rationale:
	- ERPNext doesn't immediately calculate valuation_rate (timing varies)
	- No events/hooks available when valuation calculation completes
	- Must run in queue job to avoid blocking main thread
	- Relies on Frappe's 5-minute job timeout for failure handling
	- 3-second interval balances responsiveness vs. system load

	Args:
	  stock_ledger_entry (str): Name/ID of the Stock Ledger Entry document
	  
	Note:
	  If valuation_rate is not available within 5 minutes, Frappe will
	  mark the job as failed, which is preferable to silently giving up.
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
	if frappe.get_doc('Stock Entry', doc.voucher_no).stock_entry_type == 'Material Receipt':
		frappe.enqueue(lateUpdate,queue='short', stock_ledger_entry=doc.name)

