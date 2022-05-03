for record in records:
    amt_res = 0.00
    amt_inv = 0.00
    for invoice in record.invoice_ids:
        if invoice.state=='posted':
            amt_res += invoice.amount_residual
            amt_inv += invoice.amount_total
    amt_due = (record.amount_total - amt_inv) + amt_res
    record['inv_bal_due'] = amt_due 
    total_deps = 0
    deposit_invs = []
    company_id = record.company_id and record.company_id.id or 1
    config = env['ir.config_parameter']
    setting = config.search([('key','=','sale.default_deposit_product_id')])
    setting = setting and setting[0] or None
    dep_product = setting and setting.value or None
    if dep_product:            
        try:
            dep_product = int(dep_product)                                 
        except UserError as error:
            raise UserError(error)  
        sale_dep_lines = record.order_line.search([('product_id','=',dep_product),('order_id','=',record.id)])
        for line in sale_dep_lines:
            amt_inv = 0.00
            amt_res = 0.00
            #must find the invoice corresponding with the deposit and sum the amount - residual from the invoice.
            for inv_line in line.invoice_lines:
                invoice = inv_line.move_id
                invoice_id = invoice.id
                if invoice_id not in deposit_invs:
                    deposit_invs.append(invoice_id)
                    if invoice.state=='posted':
                        amt_res += invoice.amount_residual
                        amt_inv += invoice.amount_total
                        total_deps += (amt_inv - amt_res)                
        record['deposit_total'] = total_deps
            
=======================================================================================
# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Odoo function to compare floats based on specific precisions
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - UserError: Warning Exception to use with raise
#  - Command: x2Many commands namespace
# To return an action, assign: action = {...}
records = env['sale.order'].search([('state','in', ['sale','done'])])
for record in records:
    record['open_production'] = False
    record['open_shipment'] = False
    #record['received'] = False
    #2. open_shipment if there are any undelivered items on the SO.
    for line in record.order_line:
        if line.qty_delivered < line.product_uom_qty:
            if line.product_id.type != 'service' and 'Finish Sample' not in line.name:
                if line.product_id.default_code not in ['F-FS04','F-FS01','MISC','F-CD05CH','F-CD09CH','F-CD13CH']:
                    if line.product_id.default_code not in ['F-CD14CH','F-CD18CH','F-CD19CH','F-CD40','F-CD41','DL-CD40']:
                        record['open_shipment'] = True
                        break
        else:
            record['open_shipment'] = False
    #3. open production if there are any mrp.prods that are not done.
    for mrp in record.production_ids:
        if mrp.state not in ['done','cancel']:
            record['open_production'] = True
            break
        else:
            record['open_production'] = False