from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class res_user_inventory_config(models.Model):
    _name = 'res.user.ou.config'
    _description = 'OU User Config'

    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users',string='Users', ondelete="cascade")
   
    default_ou_id = fields.Many2one(
        'operation.unit',
        string='Default Operation Unit',
    
        domain="[('id', 'in', allowed_ou_ids),('company_id', '=', company_id)]",
        required=True,
    )

    allowed_ou_ids = fields.Many2many(
        'operation.unit',
        string='Allowed Operation Units',
        domain="[('company_id', '=', company_id)]",
        required=True,
    )


    domain_company_id = fields.Char("domain_company_id",compute="compute_company_id_domain")
 
    @api.depends("user_id")
    def compute_company_id_domain(self):
      for rec in self :  
        rec.domain_company_id = [("id", "in", self.env.companies.ids)]
    

    
    @api.constrains('default_ou_id', 'allowed_ou_ids')
    def _check_default_ou(self):
        for rec in self:
            if not rec.default_ou_id:
                raise ValidationError(
                    'Each user must have a Default Operation Unit.'
                )

            if rec.default_ou_id and rec.default_ou_id not in rec.allowed_ou_ids:
                raise ValidationError(
                    'Default OU must be included in Allowed OUs'
                )
  