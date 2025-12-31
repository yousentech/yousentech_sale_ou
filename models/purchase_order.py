# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
        copy=False
    )

    
    def _prepare_picking(self):
        vals = super()._prepare_picking()

        if self.operation_unit_id:
            vals['operation_unit_id'] = self.operation_unit_id.id
            _logger.warning(
                "OU FROM PURCHASE ORDER %s → %s",
                self.name,
                vals['operation_unit_id']
            )

        return vals

    @api.model
    def create(self, vals):
        if not vals.get('operation_unit_id'):
            user = self.env.user
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
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({"operation_unit_id": self.operation_unit_id.id or False})
        return invoice_vals
 