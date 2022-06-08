# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from lxml import etree

_logger = logging.getLogger(__name__)


class ProductTemplateForm(models.Model):
    _name = 'ss_erp.product.template.form'
    _inherit = 'product.template'
    _description = 'Product Template Form'

    approval_id = fields.Char(string="Approval ID")
    approval_state = fields.Char(string='Approval status')
    product_template_id = fields.Char(string='Contact ID')

    # rewrite relation table
    taxes_id = fields.Many2many('account.tax', 'product_template_form_taxes_rel', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')], default=lambda self: self.env.company.account_sale_tax_id)
    supplier_taxes_id = fields.Many2many('account.tax', 'product_template_form_supplier_taxes_rel', 'prod_id', 'tax_id',
                                         string='Vendor Taxes', help='Default taxes used when buying the product.',
                                         domain=[('type_tax_use', '=', 'purchase')],
                                         default=lambda self: self.env.company.account_purchase_tax_id)
    route_ids = fields.Many2many(
        'stock.location.route', 'stock_route_product_template_form', 'product_id', 'route_id', 'Routes',
        domain=[('product_selectable', '=', True)],
        help="Depending on the modules installed, this will allow you to define the route of the product: whether it will be bought, manufactured, replenished on order, etc.")

    # rewrite some compute function
    # def _compute_quantities(self):
    #     products = self.filtered(lambda p: p.type != 'service' and p._name != 'ss_erp.product.template.form')
    #     res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
    #     for product in products:
    #         product.qty_available = res[product.id]['qty_available']
    #         product.incoming_qty = res[product.id]['incoming_qty']
    #         product.outgoing_qty = res[product.id]['outgoing_qty']
    #         product.virtual_available = res[product.id]['virtual_available']
    #         product.free_qty = res[product.id]['free_qty']
    #     # Services need to be set with 0.0 for all quantities
    #     services = self - products
    #     services.qty_available = 0.0
    #     services.incoming_qty = 0.0
    #     services.outgoing_qty = 0.0
    #     services.virtual_available = 0.0
    #     services.free_qty = 0.0

    def write(self, values):
        update_product_template = True
        if values.get('source', False) and values.get('source') == 'product_template':
            values.pop('source', None)
            update_product_template = False
        res = super(ProductTemplateForm, self).write(values)
        if 'approval_state' in values and values.get('approval_state') == 'approved' and update_product_template:
            self._action_process()
        return res

    def _action_process(self):
        DEFAULT_FIELDS = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date',
                          '__last_update', 'approval_id', 'approval_state', 'meeting_ids']
        for form_id in self:
            vals = {}
            for name, field in form_id._fields.items():
                if name not in DEFAULT_FIELDS and \
                        form_id._fields[name].type not in ['one2many'] and \
                        type(form_id._fields[name].compute) != str:
                    if form_id._fields[name].type == 'many2many':
                        value = getattr(form_id, name, ())
                        value = [(6, 0, value.ids)] if value else False
                    else:
                        value = getattr(form_id, name)
                        if form_id._fields[name].type == 'many2one':
                            value = value.id if value else False

                    vals.update({name: value})

            product_template_id = vals.pop('product_template_id')
            if not product_template_id:
                # Create product template form
                product_template_id = self.env['product.template'].sudo().create(vals)
                form_id.write({'product_template_id': product_template_id.id})
            else:
                # Update product template form
                vals['source'] = 'product_template_form'
                product_template = self.env['product.template'].browse(int(product_template_id))
                product_template.message_follower_ids.sudo().unlink()
                product_template.sudo().write(vals)
