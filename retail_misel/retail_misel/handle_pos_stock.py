from frappe.desk.form.linked_with import (get_linked_docs, get_linked_doctypes)
from itertools import chain
import frappe
import time

def lateUpdate(si_name):
	doc_si = frappe.get_doc('Sales Invoice', si_name)
	doc_dn = frappe.new_doc('Delivery Note')
		
	items = []
	while True:
		time.sleep(3)
		pos_invoices=frappe.get_all("POS Invoice",filters={ "consolidated_invoice": si_name },fields=["name"])	
		if pos_invoices:
			break
	for inv in pos_invoices:
		next_item = frappe.get_all('POS Invoice Item', filters={'parent': inv['name']},
			fields=['item_code', 'qty', 'name', 'custom_collected_at_pos'])
		items.append(next_item)	
	items = list(chain.from_iterable(items))	
	
	doc_dn.customer = doc_si.customer
	for item in items:
		if item.custom_collected_at_pos == 0:
			doc_sii = frappe.get_all('Sales Invoice Item', filters={'pos_invoice_item': item.name})[0]
			doc_dn.append('items',{
				'item_code':item.item_code,
				'qty': item.qty,
				'against_sales_invoice': doc_si.name,
				'si_detail': doc_sii['name'], 
			})
	doc_dn.insert()
	doc_dn.submit()

def main (doc, method):
	if doc.is_pos:
		jid = 'handle_pos_stock::{}'.format(doc.name)
		frappe.enqueue(lateUpdate,queue='long',si_name=doc.name,job_id=jid,enqueue_after_commit=True, deduplicate=False)

	
