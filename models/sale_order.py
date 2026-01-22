# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class xx_sale_order(models.Model):
    _inherit = 'sale.order'
    
    operation_unit_id = fields.Many2one('operation.unit',
                                    string='Operation Unit',
                                    copy=False)

    allowed_ou_domain = fields.Char(compute="get_allowed_ou_domain")

    @api.depends('company_id','user_id')
    def get_allowed_ou_domain(self):
        for rec in self:
            rec.allowed_ou_domain = [('id','in',self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == rec.company_id.id).allowed_ou_ids.ids)]
  
  
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        company_id = res.get('company_id', self.env.company.id)

        if not res.get('operation_unit_id'):
            ou = self.env.user.ou_config_ids.filtered(
                lambda x: x.company_id.id == company_id
            ).default_ou_id

            if ou:
                res['operation_unit_id'] = ou.id

        return res
    
    @api.onchange('company_id')
    def _onchange_company_id_set_ou(self):
        for rec in self:
            if not rec.company_id:
                rec.operation_unit_id = False
                return

            # OU الحالي غير تابع للشركة
            if rec.operation_unit_id and rec.operation_unit_id.company_id != rec.company_id:
                rec.operation_unit_id = False

            # تعيين OU افتراضي
            if not rec.operation_unit_id:
                ou = self.env.user.ou_config_ids.filtered(
                    lambda x: x.company_id == rec.company_id
                ).default_ou_id

                if ou:
                    rec.operation_unit_id = ou


    allow_modify_ou_flag = fields.Boolean(
        default=lambda self: self._default_allow_modify_ou_flag(),
        compute="_check_allow_modify_ou_flag",
    )
    def _default_allow_modify_ou_flag(self):
        
        return self.user_has_groups('yousentech_invoicing_ou.group_allow_modify_ou')

    def _check_allow_modify_ou_flag(self):
        for rec in self:
            rec.allow_modify_ou_flag = self.user_has_groups('yousentech_invoicing_ou.group_allow_modify_ou')


    @api.model
    def create(self, vals):
        if not vals.get('operation_unit_id'):
            vals['operation_unit_id'] = self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == vals.get('company_id')).default_ou_id.id
        return super().create(vals)
  
    @api.constrains('operation_unit_id')
    def _check_ou_required(self):
        for rec in self:
            if not rec.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required'
                )
    def _prepare_invoice(self):
        invoice_vals = super(xx_sale_order, self)._prepare_invoice()
        invoice_vals.update({"operation_unit_id": self.operation_unit_id.id or False})
        return invoice_vals
 
    def write(self, vals):
        if 'operation_unit_id' in vals:
            for order in self:
                invoices = order.invoice_ids.filtered(lambda m: m.state != 'cancel')

                for inv in invoices:
                    # إذا ما عليها تسوية → OK
                    reconciled_lines = inv.line_ids.filtered(
                        lambda l: l.account_id.reconcile and l.reconciled
                    )
                    if not reconciled_lines:
                        continue

                    # جلب OU الدفعات المسوّية
                    payment_ous = reconciled_lines.mapped(
                        'matched_debit_ids.move_id.operation_unit_id'
                    ) | reconciled_lines.mapped(
                        'matched_credit_ids.move_id.operation_unit_id'
                    )

                    payment_ous = payment_ous.filtered(lambda x: x)

                    # لو فيه اختلاف OU
                    if payment_ous and any(
                        ou.id != vals['operation_unit_id'] for ou in payment_ous
                    ):
                        raise ValidationError(
                            _("Cannot change Operation Unit because related payments use a different OU.")
                        )

        res = super().write(vals)

        # مزامنة الفواتير بعد التغيير
        if 'operation_unit_id' in vals:
            for order in self:
                order._sync_ou_to_invoices()

        return res


    def _sync_ou_to_invoices(self):
        for order in self:
            for inv in order.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                inv._sync_ou_from_sale_order()


    # def write(self, vals):
    #     if 'operation_unit_id' in vals:
    #         for order in self:
    #             invoices = order.invoice_ids.filtered(lambda m: m.state != 'cancel')

    #             # تحقق من وجود فواتير مُسوّاة
    #             reconciled_invoices = invoices.filtered(
    #                 lambda inv: inv.line_ids.filtered(
    #                     lambda l: l.account_id.reconcile and l.reconciled
    #                 )
    #             )

    #             if reconciled_invoices:
    #                 raise ValidationError(
    #                     _("You cannot change Operation Unit because related invoices are reconciled.")
    #                 )

    #     res = super().write(vals)

    #     # بعد التغيير → نزامن الفواتير
    #     if 'operation_unit_id' in vals:
    #         for order in self:
    #             for invoice in order.invoice_ids.filtered(lambda m: m.state != 'cancel'):
    #                 invoice._sync_ou_from_sale_order()

    #     return res
