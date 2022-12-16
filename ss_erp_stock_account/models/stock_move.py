from odoo import models, fields
from odoo.tools import float_is_zero, float_compare

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                  cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)

        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            if self.picking_id.x_inventory_journal_date:
                date = self.picking_id.x_inventory_journal_date
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'x_organization_id': self.x_organization_id.id,
                'x_responsible_dept_id': self.x_responsible_dept_id.id,
                'x_responsible_user_id': self.x_responsible_user_id.id,
                'x_account_modify': self.picking_id.x_account_modify,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    def _get_price_unit(self):
        if self.instruction_order_line_id:
            return self.instruction_order_line_id.product_cost
        else:
            return super()._get_price_unit()

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.uom_id)
            unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard' and not move.instruction_order_id:
                unit_cost = move.product_id.standard_price
            svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                if move.lpgas_adjustment:
                    svl_vals[
                        'description'] = self.name
                else:
                    svl_vals[
                        'description'] = 'INV：%s - %s' % (move.picking_id.name or move.name or move.instruction_order_id.name, move.product_id.product_tmpl_id.name)
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
                continue
            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                if move.lpgas_adjustment:
                    svl_vals[
                        'description'] = self.name
                else:
                    svl_vals[
                        'description'] = 'INV：%s - %s' % (move.picking_id.name or move.name or move.instruction_order_id.name, move.product_id.product_tmpl_id.name)
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)