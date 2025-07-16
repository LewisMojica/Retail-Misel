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

def lateUpdate(stock_ledger_entry, update_selling_rate):
	"""
	Updates Item valuation_rate field after ERPNext completes valuation calculation.

	This function uses polling because ERPNext's valuation calculation is asynchronous
	and doesn't provide hooks/events when completed. The valuation_rate is stored in
	Stock Ledger Entry but needs to be synchronized to the Item doctype.

	Optionally updates the selling rate (standard_rate) proportionally based on the
	ratio between the old standard_rate and old valuation_rate.

	Polling approach rationale:
	- ERPNext doesn't immediately calculate valuation_rate (timing varies)
	- No events/hooks available when valuation calculation completes
	- Must run in queue job to avoid blocking main thread
	- Relies on Frappe's 5-minute job timeout for failure handling
	- 3-second interval balances responsiveness vs. system load

	Args:
		 stock_ledger_entry (str): Name/ID of the Stock Ledger Entry document
		 update_selling_rate (bool): Whether to proportionally update the Item's standard_rate
											 based on the valuation rate change

	Note:
		 If valuation_rate is not available within 5 minutes, Frappe will
		 mark the job as failed, which is preferable to silently giving up.
		 
		 Selling rate calculation maintains the original ratio between standard_rate
		 and valuation_rate when updating costs.
	"""
	import time
	def getItemPrice(item_code):
		return frappe.get_all("Item Price", filters={"item_code": item_code,	"price_list": "Standard Selling"}, fields=['name',"price_list_rate"])[0]
		
	def getNewSellingRate(item_code, new_valuation):
		"""
		Calculate new selling rate maintaining the original ratio to valuation rate.

		Args:
			 item_code (str): Item code to update
			 new_valuation (float): New valuation rate
			 
		Returns:
			 float: New selling rate proportional to valuation change
		"""
		ratio = getItemPrice(item_code)['price_list_rate'] / frappe.get_value('Item', item_code, 'valuation_rate')
		return ratio * new_valuation
		
	while True:	
		time.sleep(3)
		valuation_rate = frappe.get_value('Stock Ledger Entry', stock_ledger_entry, 'valuation_rate')
		if valuation_rate != None:
			item_code = frappe.get_value('Stock Ledger Entry', stock_ledger_entry, 'item_code')
			if update_selling_rate: 
				item_price = getItemPrice(item_code)
				frappe.set_value('Item Price', item_price['name'], 'price_list_rate', getNewSellingRate(item_code, valuation_rate))
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
		frappe.enqueue(lateUpdate,queue='short', stock_ledger_entry=doc.name, update_selling_rate=True)

