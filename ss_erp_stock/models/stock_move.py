from odoo import models, fields
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_order_line_id = fields.Many2one('ss_erp.inventory.order.line', string="移動オーダ明細")
    instruction_order_id = fields.Many2one('ss_erp.instruction.order', string="棚卸計画")
    instruction_order_line_id = fields.Many2one('ss_erp.instruction.order.line', string="棚卸計画明細")

    product_packaging = fields.Many2one(string='パッケージ', related='inventory_order_line_id.product_packaging', store=True)
    x_organization_id = fields.Many2one('ss_erp.organization',
                                      string='組織名', store=True)

    x_responsible_dept_id = fields.Many2one('ss_erp.responsible.department',
                                                 related='picking_id.x_responsible_dept_id', string='管轄部門', store=True)

    lpgas_adjustment = fields.Boolean(string='', default=False)

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
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
            unit_cost = abs(move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard' and not move.instruction_order_id:
                unit_cost = move.product_id.standard_price
            svl_vals = move.product_id._prepare_in_svl_vals(forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    # def _get_accounting_data_for_valuation(self):
    #     rec = super()._get_accounting_data_for_valuation()
    #
    #     if self.location_id.scrap_location:
    #         if not self.location_id.valuation_out_account_id:
    #             raise UserError('在庫評価勘定(出庫)の勘定を定義してください。')
    #         account_lst = list(rec)[:-1]
    #         account_lst.append(self.location_id.valuation_out_account_id.id)
    #         return tuple(account_lst)
    #     else:
    #         return rec

    def _is_in(self):
        if not self.lpgas_adjustment:
            return super()._is_in()
        else:
            if self.location_id.usage == 'inventory':
                return True
            else:
                return False

    def _is_out(self):
        if not self.lpgas_adjustment:
            return super()._is_out()
        else:
            if self.location_dest_id.usage == 'inventory':
                return True
            else:
                return False

    # def _get_accounting_data_for_valuation(self):
    #     if not self.lpgas_adjustment:
    #         return super()._get_accounting_data_for_valuation()
    #     else:
    #         self.ensure_one()
    #         self = self.with_company(self.company_id)
    #         accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
    #         journal_id = accounts_data['stock_journal'].id
    #
    #         acc_src = self.location_id.valuation_out_account_id.id if self.location_id.usage == 'inventory' else self._get_src_account(accounts_data)
    #         acc_dest = self.location_id.valuation_in_account_id.id if self.location_id.usage == 'inventory' else self._get_dest_account(accounts_data)
    #
    #         acc_valuation = accounts_data.get('stock_valuation', False).id
    #
    #         return journal_id, acc_src, acc_dest, acc_valuation



