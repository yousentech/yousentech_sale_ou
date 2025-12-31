# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
 
class AccountMove(models.Model):
    _inherit ='account.move'
 
    @api.constrains('invoice_line_ids', 'operation_unit_id')
    def _check_single_ou(self):
        for move in self:
            ous = self.env['operation.unit']

            # 1️⃣ OU من الفاتورة نفسها
            if move.operation_unit_id:
                ous |= move.operation_unit_id

            # 2️⃣ OU من سطور الفاتورة
            for line in move.invoice_line_ids:
                if line.operation_unit_id:
                    ous |= line.operation_unit_id

                # من sale order
                if line.sale_line_ids:
                    ous |= line.sale_line_ids.mapped(
                        'order_id.operation_unit_id'
                    )

                
            ous = ous.filtered(lambda x: x)

            if len(ous) > 1:
                raise ValidationError(
                    _('You cannot mix multiple Operation Units in one invoice.')
                )

                