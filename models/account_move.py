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
 
    
    def _sync_ou_from_sale_order(self):
        for move in self:
            sale_orders = move.invoice_line_ids.mapped(
                'sale_line_ids.order_id'
            ).filtered(lambda x: x)

            if len(sale_orders) != 1:
                continue

            sale = sale_orders[0]
            ou = sale.operation_unit_id

            if not ou:
                continue
            # لو الفاتورة OU فاضي → نملأه
            move.write({
                'operation_unit_id': sale.operation_unit_id.id
            })
            move.line_ids.write({
                'operation_unit_id': sale.operation_unit_id.id
            })

            # لو عليها دفعات → نزامن الدفعات
            move._sync_ou_to_payments()

    def _sync_ou_to_payments(self):
        for move in self:
            payments = move.line_ids.mapped(
                'matched_debit_ids.move_id'
            ) | move.line_ids.mapped(
                'matched_credit_ids.move_id'
            )

            payments = payments.filtered(lambda m: m.payment_id)

            for pay_move in payments:
                payment = pay_move.payment_id
                if not payment.operation_unit_id:
                    payment.write({
                        'operation_unit_id': move.operation_unit_id.id
                    })


