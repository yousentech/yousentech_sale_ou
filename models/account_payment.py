# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class AccountPayment(models.Model):
    _inherit =  'account.payment' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
     
        copy=False
    )

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
