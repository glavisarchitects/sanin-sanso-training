from odoo import models, fields


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
