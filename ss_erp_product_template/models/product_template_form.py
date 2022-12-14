# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from lxml import etree
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ProductTemplateForm(models.Model):
    _name = 'ss_erp.product.template.form'
    _inherit = 'product.template'
    _description = 'Product Template Form'

    type = fields.Selection([
        ('product', 'Storable Product'),
        ('consu', 'Consumable'),
        ('service', 'Service')], string='Product Type', default='consu', required=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
    invoice_policy = fields.Selection([
        ('order', 'Ordered quantities'),
        ('delivery', 'Delivered quantities')], string='Invoicing Policy',
        help='Ordered Quantity: Invoice quantities ordered by the customer.\n'
             'Delivered Quantity: Invoice quantities delivered to the customer.',
        default='order')
    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Policy", help="On ordered quantities: Control bills based on ordered quantities.\n"
                                     "On received quantities: Control bills based on received quantities.",
        default="receive")

    approval_id = fields.Char(string="Approval ID")
    approval_state = fields.Char(string='Approval status')
    product_template_id = fields.Char(string='Template ID', copy=False)

    # rewrite relation table
    taxes_id = fields.Many2many('account.tax', 'ss_erp_product_template_form_taxes_rel', 'prod_id', 'tax_id',
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                default=lambda self: self.env.company.account_sale_tax_id)
    supplier_taxes_id = fields.Many2many('account.tax', 'ss_erp_product_template_form_supplier_taxes_rel', 'prod_id', 'tax_id',
                                         string='Vendor Taxes', help='Default taxes used when buying the product.',
                                         default=lambda self: self.env.company.account_purchase_tax_id)
    route_ids = fields.Many2many(
        'stock.location.route', 'ss_erp_stock_route_product_template_form', 'product_id', 'route_id', 'Routes',
        help="Depending on the modules installed, this will allow you to define the route of the product: whether it will be bought, manufactured, replenished on order, etc.")

    optional_product_ids = fields.Many2many(
        'product.template', 'ss_erp_product_template_form_optional_rel', 'src_id', 'dest_id',
        string='Optional Products', help="Optional Products are suggested "
                                         "whenever the customer hits *Add to Cart* (cross-sell strategy, "
                                         "e.g. for computers: warranty, software, etc.).", check_company=True)
    # change o2m to m2m
    x_product_unit_measure_ids = fields.Many2many('ss_erp.product.units.measure', string='????????????', tracking=True)
    user_id = fields.Many2one(
        comodel_name='res.users', default=lambda self: self.env.uid)
    # rewrite some compute function
    @api.depends_context('company', 'location', 'warehouse')
    def _compute_quantities(self):
        for template in self:
            template.qty_available = 0
            template.virtual_available = 0
            template.incoming_qty = 0
            template.outgoing_qty = 0

    def write(self, values):
        update_product_template = True
        if values.get('source', False) and values.get('source') == 'product_template':
            values.pop('source', None)
            update_product_template = False
        res = super(ProductTemplateForm, self).write(values)
        if 'approval_state' in values and values.get('approval_state') == 'approved' and update_product_template:
            self._action_process()
        return res

    @api.constrains('name')
    def _check_product_name(self):
        for product in self:
            if self.search_count([('name', '=', product.name)]) > 1:
                raise UserError('????????????????????????????????????????????????????????????????????????????????????')

    def _action_process(self):
        DEFAULT_FIELDS = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date',
                          '__last_update', 'approval_id', 'approval_state', 'meeting_ids']
        for form_id in self:
            vals = {}
            for name, field in form_id._fields.items():

                # Bug 189
                value = False
                if name not in self.env['product.template']._fields and name != 'product_template_id':
                    continue
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
                new_product_template = self.env['product.template'].sudo().create(vals)
                form_id.write({'product_template_id': new_product_template.id})
            else:
                # Update product template form
                vals['source'] = 'product_template_form'
                product_template = self.env['product.template'].browse(int(product_template_id))
                product_template.message_follower_ids.sudo().unlink()
                product_template.sudo().write(vals)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = [('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
