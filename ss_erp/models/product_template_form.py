# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from lxml import etree
from odoo.osv import expression
import re

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


    optional_product_ids = fields.Many2many(
        'product.template', 'product_template_form_optional_rel', 'src_id', 'dest_id',
        string='Optional Products', help="Optional Products are suggested "
        "whenever the customer hits *Add to Cart* (cross-sell strategy, "
        "e.g. for computers: warranty, software, etc.).", check_company=True)
    # change o2m to m2m
    x_product_unit_measure_ids = fields.Many2many('ss_erp.product.units.measure',string='代替単位', tracking=True)

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

    def _action_process(self):
        DEFAULT_FIELDS = ['id', 'create_uid', 'create_date', 'write_uid', 'write_date',
                          '__last_update', 'approval_id', 'approval_state', 'meeting_ids']
        for form_id in self:
            vals = {}
            for name, field in form_id._fields.items():
                if name not in self.env['product.template']._fields:
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

            if 'product_template_id' not in vals:
                # Create product template form
                new_product_template = self.env['product.template'].sudo().create(vals)
                form_id.write({'product_template_id': new_product_template.id})
            else:
                # Update product template form
                product_template_id = vals.pop('product_template_id')
                vals['source'] = 'product_template_form'
                product_template = self.env['product.template'].browse(int(product_template_id))
                product_template.message_follower_ids.sudo().unlink()
                product_template.sudo().write(vals)


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return product_ids
