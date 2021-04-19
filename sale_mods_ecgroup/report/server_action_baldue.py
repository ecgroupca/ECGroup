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
        config = self.env['ir.config_parameter']
        setting = config.search([('key','=','sale.default_deposit_product_id')])
        setting = setting and setting[0] or None
        dep_product = setting and setting.value or None
        if dep_product:            
            try:
                dep_product = int(dep_product)                                 
            except UserError as error:
                raise UserError(error)  
            sale_dep_lines = self.order_line.search([('product_id','=',dep_product),('order_id','=',record.id)])
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