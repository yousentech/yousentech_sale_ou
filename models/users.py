# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    ou_config_ids = fields.One2many(
        'res.user.ou.config','user_id',
        string='Inventory Defaults'
    ) 
    
