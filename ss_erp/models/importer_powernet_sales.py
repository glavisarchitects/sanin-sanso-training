# -*- coding: utf-8 -*-
import calendar
import pandas as pd
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

MODELS_CUSTOM_IMPORTS = [
    'ss_erp.ifdb.powernet.sales.header',
]

# csv columns
CSV_FIELDS = ['id', 'name', 'branch_id', 'user_id','upload_date',
              'customer_code','billing_summary_code', 'sales_date', 'slip_type',
              'slip_no', 'data_types', 'cash_classification','product_code','product_name',
              'sales_category', 'quantity', 'unit_code', 'unit_price', 'amount_of_money',
              'consumption_tax', 'sales_amount', 'quantity_after_conversion','search_remarks_1','search_remarks_2',
              'search_remarks_3','search_remarks_4','search_remarks_5','search_remarks_6','search_remarks_7','search_remarks_8']

# custom columns
CUSTOM_FIELDS_IMPORTS = [
    'id',  # External ID
    'name',
    'branch_id',
    'user_id',
    'upload_date',
    'powernet_sale_record_ids/customer_code',
    'powernet_sale_record_ids/billing_summary_code',
    'powernet_sale_record_ids/sales_date',
    'powernet_sale_record_ids/slip_type',
    'powernet_sale_record_ids/slip_no',
    'powernet_sale_record_ids/data_types',
    'powernet_sale_record_ids/cash_classification',
    'powernet_sale_record_ids/product_code',
    'powernet_sale_record_ids/product_name',
    'powernet_sale_record_ids/sales_category',
    'powernet_sale_record_ids/quantity',
    'powernet_sale_record_ids/unit_code',
    'powernet_sale_record_ids/unit_price',
    'powernet_sale_record_ids/amount_of_money',
    'powernet_sale_record_ids/consumption_tax',
    'powernet_sale_record_ids/sales_amount',
    'powernet_sale_record_ids/quantity_after_conversion',
    'powernet_sale_record_ids/search_remarks_1',
    'powernet_sale_record_ids/search_remarks_2',
    'powernet_sale_record_ids/search_remarks_3',
    'powernet_sale_record_ids/search_remarks_4',
    'powernet_sale_record_ids/search_remarks_5',
    'powernet_sale_record_ids/search_remarks_6',
    'powernet_sale_record_ids/search_remarks_7',
    'powernet_sale_record_ids/search_remarks_8',

]


def _convert_YMD(int_date):
    # convert 210203 to 20210203
    data = '20' + str(int_date).strip()
    if len(data) < 4:
        return ''
    dt = str(datetime.strptime(data, '%Y%m%d')).replace(' 00:00:00', '')
    return dt


class Importer(models.TransientModel):
    _inherit = 'base_import.import'
    _description = 'PowerNet Sales Import'

    def _format_csv(self, df):
        for index in range(0, len(df)):
            # Header field
            sales_date = str(df.at[index, 'powernet_sale_record_ids/sales_date']).replace(' ', '')
            upload_date = str(df.at[index, 'upload_date']).replace(' ', '')
            df.loc[index, 'powernet_sale_record_ids/customer_code'] = df.loc[index, 'powernet_sale_record_ids/customer_code']
            df.loc[index, 'powernet_sale_record_ids/billing_summary_code'] = df.loc[index, 'powernet_sale_record_ids/billing_summary_code']
            df.loc[index, 'powernet_sale_record_ids/slip_type'] = df.loc[index, 'powernet_sale_record_ids/slip_type']
            df.loc[index, 'powernet_sale_record_ids/slip_no'] = df.loc[index, 'powernet_sale_record_ids/slip_no']
            df.loc[index, 'powernet_sale_record_ids/data_types'] = df.loc[index, 'powernet_sale_record_ids/data_types']
            df.loc[index, 'powernet_sale_record_ids/sales_date'] = _convert_YMD(sales_date)
            df.loc[index, 'id'] = df.loc[index, 'id']
            df.loc[index, 'name'] = df.loc[index, 'name']
            df.loc[index, 'user_id'] = df.loc[index, 'user_id']
            df.loc[index, 'branch_id'] = df.loc[index, 'branch_id']
            df.loc[index, 'upload_date'] = _convert_YMD(upload_date)  # not insert/update

        return df

    #
    def _mapping(self, datas):
        df = pd.DataFrame(datas)
        df.replace('N/A', '')

        df['id'] = ''
        df['name'] = ''
        df['user_id'] = ''
        df['branch_id'] = ''
        df['upload_date'] = ''

        df['powernet_sale_record_ids/sales_date'] = ''
        df['powernet_sale_record_ids/billing_summary_code'] = ''
        df['powernet_sale_record_ids/customer_code'] = ''
        df['powernet_sale_record_ids/slip_type'] = ''
        df['powernet_sale_record_ids/slip_no'] = ''
        df['powernet_sale_record_ids/data_types'] = ''

        # verify null data and fomarter
        df = self._format_csv(df)

        return df

    #
    def _read_file(self, options):
        res = super(Importer, self)._read_file(options)
        # HEADER
        if options.get('import_custom'):
            yield CUSTOM_FIELDS_IMPORTS
            # BODY
            res_cleaners = self._mapping(datas=res)
            for row in res_cleaners.itertuples(index=False, name=None):
                yield row
        else:
            for row in res:
                yield row
        # ==================== END OF BODY DATA STANDARD=======================

    # btn smart import
    def import_data_custom(self, options):
        # self.ensure_one()
        self.parse_preview(options)


