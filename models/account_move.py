# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
 
class AccountMove(models.Model):
    _inherit ='account.move'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False )

    @api.model
    def create(self, vals):
       
        if not vals.get('operation_unit_id'):
            vals['operation_unit_id'] =  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == vals.get('company_id')).default_ou_id.id

        return super().create(vals)
 
   
    @api.constrains('invoice_line_ids')
    def _check_single_ou(self):
        for move in self:
            ous = move.invoice_line_ids.mapped(
                'sale_line_ids.order_id.operation_unit_id'
            )
            ous |= move.invoice_line_ids.mapped(
                'purchase_line_id.order_id.operation_unit_id'
            )
            ous = ous.filtered(lambda x: x)
            if len(ous) > 1:
                raise ValidationError(
                    'You cannot mix multiple Operation Units in one invoice'
                )

                
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'move Operation Unit is required'
                )
 
    def _get_outstanding_info_JSON(self):
        self.ensure_one()
        result = super()._get_outstanding_info_JSON()
    
        # لو ما فيه OU على الفاتورة أو ما فيه مدفوعات
        if not self.operation_unit_id or not result or not result.get('content'):
            return result

        invoice_ou_id = self.operation_unit_id.id
        filtered_content = []

        for line in result['content']:
            aml_id = line.get('line_id')
            if not aml_id:
                continue

            aml = self.env['account.move.line'].browse(aml_id)

            # نعرض فقط المدفوعات التابعة لنفس OU
            if aml.operation_unit_id and aml.operation_unit_id.id == invoice_ou_id:
                filtered_content.append(line)

        result['content'] = filtered_content
        return result
     
    @api.constrains('operation_unit_id', 'company_id')
    def _check_operation_unit_validity(self):
        for move in self:
            ou = move.operation_unit_id
            user = self.env.user

            if not ou:
                raise ValidationError("Operation Unit is required on this document.")
 
            if ou.company_id != move.company_id:
                raise ValidationError(
                    "The selected Operation Unit does not belong to the same company as this document."
                ) 

            if user.ou_config_ids.filtered(lambda x: x.company_id.id == move.company_id.id).allowed_ou_ids and ou not in user.ou_config_ids.filtered(lambda x: x.company_id.id == move.company_id.id).allowed_ou_ids:

                raise ValidationError(
                    "The selected Operation Unit is not allowed for the current user."
                )

    def action_post(self):
        for move in self:
            if not move.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required before posting the accounting entry.'
                )
        return super().action_post()

 
class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='line_ids.move_id.operation_unit_id',
        copy=False )

    def _init_payments(self, to_process, edit_mode=False):
        # 🔹 حقن OU في قيم الإنشاء
        for vals in to_process:
            create_vals = vals.get('create_vals', {})

            if self.operation_unit_id:
                create_vals['operation_unit_id'] = self.operation_unit_id.id

        # 🔹 نكمل السلوك الأصلي
        return super()._init_payments(to_process, edit_mode=edit_mode)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='move_id.operation_unit_id',
        store=True,
        copy=False
    )


    # @api.constrains('operation_unit_id')
    # def _check_ou_required(self):
    #     for line in self:
    #         if not line.operation_unit_id:
    #             raise ValidationError(
    #                 'Operation Unit is required on journal items.'
    #             )
    # @api.model
    # def create(self, vals):

    #     if not vals.get('operation_unit_id'):
    #         if vals.get('move_id'):
    #             move = self.env['account.move'].browse(vals['move_id'])
    #             if move.operation_unit_id:
    #                 vals['operation_unit_id'] = move.operation_unit_id.id

    #     # if not vals.get('operation_unit_id'):
    #     #     vals['operation_unit_id'] = self.env.user.default_ou_id.id

    #     return super().create(vals)
    
    def reconcile(self):
        ous = self.mapped('operation_unit_id').filtered(lambda x: x)
     
        if len(ous) > 1:
            raise ValidationError(
                'You cannot reconcile entries from different Operation Units.'
            )
        return super().reconcile()
