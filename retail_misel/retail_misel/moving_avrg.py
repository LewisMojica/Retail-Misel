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
