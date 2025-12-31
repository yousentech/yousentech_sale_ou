# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class OperationUnit(models.Model):
    _name = 'operation.unit'
    _description = 'Operation Unit'
 
    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(default=True)
