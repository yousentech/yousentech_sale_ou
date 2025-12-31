# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
       
        copy=False
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.operation_unit_id:
            res.operation_unit_id = self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == res.company_id.id).default_ou_id.id

        return res


    def button_validate(self):
        for picking in self:
            if not picking.operation_unit_id:
                raise ValidationError(
                    'Operation Unit is required before validating the picking.'
                )

            ou = picking.operation_unit_id
            user = self.env.user

            if not ou:
                raise ValidationError("Operation Unit is required on this document.")

            if ou.company_id != picking.company_id:
                raise ValidationError(
                    "The selected Operation Unit does not belong to the same company as this document."
                )

            if user.ou_config_ids.filtered(lambda x: x.company_id.id == picking.company_id.id).allowed_ou_ids and ou not in user.ou_config_ids.filtered(lambda x: x.company_id.id == picking.company_id.id).allowed_ou_ids:
                raise ValidationError(
                    "The selected Operation Unit is not allowed for the current user."
                )
           
            picking._assign_ou_to_moves()

        return super().button_validate()


    def _assign_ou_to_moves(self):
        for picking in self:
            if picking.operation_unit_id:
                for line in picking.move_ids_without_package:
                    line.write({
                            'operation_unit_id': picking.operation_unit_id.id
                        })

 
class StockMove(models.Model):
    _inherit = 'stock.move' 

    operation_unit_id = fields.Many2one(
        'operation.unit',
        readonly=True,
       
        copy=False
    )


    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()

        # من أمر البيع
        if self.sale_line_id and self.sale_line_id.order_id.operation_unit_id:
            vals['operation_unit_id'] = self.sale_line_id.order_id.operation_unit_id.id
            _logger.warning(
                "OU FROM SALE ORDER %s → %s",
                self.sale_line_id.order_id.name,
                vals['operation_unit_id']
            )
            return vals

        # من أمر الشراء
        if self.purchase_line_id and self.purchase_line_id.order_id.operation_unit_id:
            vals['operation_unit_id'] = self.purchase_line_id.order_id.operation_unit_id.id
            _logger.warning(
                "OU FROM PURCHASE ORDER %s → %s",
                self.purchase_line_id.order_id.name,
                vals['operation_unit_id']
            )
            return vals

        # fallback
        vals['operation_unit_id'] =  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == self.company_id.id).default_ou_id.id
        _logger.warning(
            "OU FROM USER DEFAULT → %s",
            vals['operation_unit_id']
        )
        return vals
 
 
    def _prepare_account_move_vals(self):
        vals = super()._prepare_account_move_vals()

        ou = False
 
        if self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id
 
        if not ou and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id
 
        if not ou:
            ou =  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == self.company_id.id).default_ou_id
 
        if ou:
            vals['operation_unit_id'] = ou.id

        return vals
        
    def _prepare_account_move_vals(self, acc_valuation,  acc_dest,  journal_id, qty,  description, svl_id,cost ):
        vals = super()._prepare_account_move_vals(
            acc_valuation,
            acc_dest,
            journal_id,
            qty,
            description,
            svl_id,
            cost
        )

        ou = False

        # 1️⃣ من valuation layer
        if self.stock_valuation_layer_ids:
            ou = self.stock_valuation_layer_ids[0].operation_unit_id

        # 2️⃣ من picking
        if not ou and self.picking_id and self.picking_id.operation_unit_id:
            ou = self.picking_id.operation_unit_id

        # 3️⃣ fallback
        if not ou:
            ou =  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == self.company_id.id).default_ou_id

        if ou:
            vals['operation_unit_id'] = ou.id

        return vals

   
    def _prepare_account_move_line( self, qty, cost, credit_account_id, debit_account_id,  svl_id, description):
        lines = super()._prepare_account_move_line(
            qty,
            cost,
            credit_account_id,
            debit_account_id,
            svl_id,
            description
        )

        ou = (
            self.stock_valuation_layer_ids[:1].operation_unit_id
            or self.picking_id.operation_unit_id
            or  self.env.user.ou_config_ids.filtered(lambda x: x.company_id.id == self.company_id.id).default_ou_id
        )

        if ou:
            for line in lines:
                line[2]['operation_unit_id'] = ou.id

        return lines

        



class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    operation_unit_id = fields.Many2one(
        'operation.unit',
        string='Operation Unit',
        readonly=True,
        related='stock_move_id.operation_unit_id',
        store=True,
        copy=False
    )


