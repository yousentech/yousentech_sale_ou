# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class xx_sale_order(models.Model):
    _inherit = 'sale.order'
    
    operation_unit_id = fields.Many2one('operation.unit',
                                    string='Operation Unit',
                                    copy=False,domain=[('share_ou','=',False)])

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

                # تحقق من وجود فواتير مُسوّاة
                reconciled_invoices = invoices.filtered(
                    lambda inv: inv.line_ids.filtered(
                        lambda l: l.account_id.reconcile and l.reconciled
                    )
                )

                if reconciled_invoices:
                    raise ValidationError(
                        _("You cannot change Operation Unit because related invoices are reconciled.")
                    )

        res = super().write(vals)

        # بعد التغيير → نزامن الفواتير
        if 'operation_unit_id' in vals:
            for order in self:
                for invoice in order.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                    invoice._sync_ou_from_sale_order()

        return res
 
    @api.constrains('operation_unit_id', 'company_id')
    def _check_ou_company(self):
        for rec in self:
            if rec.operation_unit_id and rec.company_id:
                if rec.operation_unit_id.company_id != rec.company_id:
                    raise ValidationError(
                        "Operation Unit must belong to the selected company."
                    )
 
 