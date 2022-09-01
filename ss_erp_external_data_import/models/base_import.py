from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

try:
    import pandas as pd
    import numpy as np
except (ImportError, ModuleNotFoundError):
    raise UserError(_(
        "pandas / numpy extension libraries not found. Please install by command: \n"
        "pip3 install numpy\n"
        "pip3 install pandas\n"
    ))

FIELDS_BEFORE_ifdb_yg = [
    'item',
    'customer_cd',
    'meter_reading_date',
    'amount_use',
]

FIELDS_AFTER_ifdb_yg = [
    'header_id/ Database ID',
    'item',
    'customer_cd',
    'meter_reading_date',
    'amount_use',
]

FIELDS_BEFORE_ifdb_yg_summary = [
    'partner_id',
    'amount_use',
    'item',

]

FIELDS_AFTER_ifdb_yg_summary = [
    'header_id/ Database ID',
    'partner_id',
    'amount_use',
    'item',

]

FIELDS_MODEL = {
    'ss_erp.ifdb.yg.summary': {
        'FIELDS_BEFORE': FIELDS_BEFORE_ifdb_yg_summary,
        'FIELDS_AFTER': FIELDS_AFTER_ifdb_yg_summary
    },
    'ss_erp.ifdb.yg.detail': {
        'FIELDS_BEFORE': FIELDS_BEFORE_ifdb_yg,
        'FIELDS_AFTER': FIELDS_AFTER_ifdb_yg
    }
}


class Import(models.TransientModel):
    _inherit = "base_import.import"
    _description = "Base Import"

    import_file_header_model = fields.Char(
        string="Related File Header Model",
        readonly=True,
        index=True
    )
    import_file_header_id = fields.Many2oneReference(
        string="Related File Header Id",
        readonly=True,
        index=True,
        model_field="import_file_header_model"
    )

    x_header_account_transfer = fields.Char(
        string="Data Header",
        readonly=True,
    )
    x_header_account_receipt = fields.Char(string="Data Header",readonly=True)

    def _get_ifdb_file_header(self, parent_context):
        self.ensure_one()
        if (
                parent_context and
                not any([self.import_file_header_id, self.import_file_header_model])
        ):
            self.import_file_header_model = parent_context["default_import_file_header_model"]
            self.import_file_header_id = parent_context["default_import_file_header_id"]
        file_header = self.env[self.import_file_header_model].browse(
            self.import_file_header_id
        )
        if not file_header:
            raise UserError(
                _("Missing File Header, please using `upload` option from file header!")
            )
        return file_header

    def transform_autogas_file(self, options, parent_context={}):
        autogas_header = self._get_ifdb_file_header(parent_context)
        encode = "Shift-JIS"
        if options.get('encoding'):
            encode = options.get('encoding')
        data = self.file.decode(encode).split("\r\n")
        # remove the first and last line
        data = data[1:-2]
        new_data = [
            '"card_classification","processing_division","unused","group_division",' + \
            '"actual_car_number","card_number","product_code","data_no","quantity_1",' + \
            '"unit_price","amount_of_money","staff_code","processing_time","calendar_date",' + \
            '"consumption_tax_output_classification","consumption_tax",' + \
            '"credit_terminal_processing_serial_number","credit_classification",' + \
            '"credit_data_no","tax_classification_code","filer1","quantity_2",' + \
            '"filer2","autogas_file_header_id"'
        ]
        for line in data:
            line_data, quantity_2 = line.split()
            card_classification = line_data[0]
            processing_division = line_data[1:3]
            unused = line_data[3:5]
            group_division = line_data[5:6]
            actual_car_number = line_data[6:10]
            card_number = line_data[10:25]
            product_code = line_data[25:30]
            data_no = line_data[30:34]
            quantity_1 = line_data[34:40]
            unit_price = line_data[40:48]
            amount_of_money = line_data[48:55]
            staff_code = line_data[55:57]
            processing_time = line_data[57:61]
            calendar_date = line_data[61:67]
            consumption_tax_output_classification = line_data[67:68]
            consumption_tax = line_data[68:75]
            credit_terminal_processing_serial_number = line_data[75:80]
            credit_classification = line_data[80:81]
            credit_data_no = line_data[81:85]
            tax_classification_code = line_data[85:86]
            filer1 = ""
            filer2 = ""
            new_line_data = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"' % (
                card_classification,
                processing_division,
                unused,
                group_division,
                actual_car_number,
                card_number,
                product_code,
                data_no,
                quantity_1,
                unit_price,
                amount_of_money,
                staff_code,
                processing_time,
                calendar_date,
                consumption_tax_output_classification,
                consumption_tax,
                credit_terminal_processing_serial_number,
                credit_classification,
                credit_data_no,
                tax_classification_code,
                filer1,
                quantity_2,
                filer2,
                autogas_header.name,
            )
            new_data.append(new_line_data)

        self.file = "\n".join(new_data).encode(encode)

    def transform_powernet_file(self, options, parent_context={}):
        powernet_header = self._get_ifdb_file_header(parent_context)
        data = self.file.split(b"\n")
        new_data = [
            b'"powernet_sales_header_id","customer_code","billing_summary_code",' + \
            b'"sales_date","slip_type","slip_no","data_types","cash_classification",' + \
            b'"product_code","product_code_2","product_name","product_remarks",' + \
            b'"sales_category","quantity","unit_code","unit_price","amount_of_money",' + \
            b'"consumption_tax","sales_amount","quantity_after_conversion",' + \
            b'"search_remarks_1","search_remarks_2","search_remarks_3","search_remarks_4",' + \
            b'"search_remarks_5","search_remarks_6","search_remarks_7","search_remarks_8",' + \
            b'"search_remarks_9","search_remarks_10","sales_classification_code_1",' + \
            b'"sales_classification_code_2","sales_classification_code_3",' + \
            b'"consumer_sales_classification_code_1","consumer_sales_classification_code_2",' + \
            b'"consumer_sales_classification_code_3","consumer_sales_classification_code_4",' + \
            b'"consumer_sales_classification_code_5","product_classification_code_1",' + \
            b'"product_classification_code_2","product_classification_code_3"'
        ]
        encode = "Shift-JIS"
        if options.get('encoding'):
            encode = options.get('encoding')
        for line in data:
            if line == b"":
                continue
            new_line = b'"%s",' % (powernet_header.name.encode(encode)) + line
            new_data.append(new_line)
        self.file = b"\n".join(new_data)

    def transform_youki_kanri_file(self, options, parent_context={}):
        youki_kanri = self._get_ifdb_file_header(parent_context)
        data = self.file.split(b"\n")
        new_data = [
            b'"ifdb_youki_kanri_id","external_data_type","customer_branch_code",' + \
            b'"customer_branch_sub_code","customer_business_partner_code",' + \
            b'"customer_business_partner_branch_code","customer_delivery_code",' + \
            b'"direct_branch_code","direct_branch_sub_code","direct_business_partner_code",' + \
            b'"direct_business_partner_sub_code","direct_delivery_code","customer_name",' + \
            b'"codeommercial_branch_code","codeommercial_branch_sub_code",' + \
            b'"codeommercial_product_code","product_name","standard_name","standard",' + \
            b'"number","slip_date","codelassification_code","line_break","quantity",' + \
            b'"unit_code","unit_price","amount_of_money","unit_price_2","amount_2",' + \
            b'"unified_quantity","order_number","comment","codeommercial_branch_code2",' + \
            b'"codeommercial_branch_sub_code2","codeommercial_product_code2",' + \
            b'"amount_calculation_classification","slip_processing_classification"'
        ]
        encode = "Shift-JIS"
        if options.get('encoding'):
            encode = options.get('encoding')
        for line in data:
            if line == b"":
                continue
            new_line = b'"%s",' % (youki_kanri.name.encode(encode)) + line
            new_data.append(new_line)
        self.file = b"\n".join(new_data)

    def transform_youki_kensa_file(self, options, parent_context={}):
        youki_kensa = self._get_ifdb_file_header(parent_context)
        data = self.file.split(b"\n")[1:]
        new_data = [
            b'"youkikensa_billing_file_header_id","sales_date","slip_no","field_3",' + \
            b'"billing_code","billing_abbreviation","customer_code",' + \
            b'"customer_abbreviation","product_code","product_name","unit_price",' + \
            b'"return_quantity_for_sale","net_sales_excluding_tax","consumption_tax",' + \
            b'"remarks","unit_cost","description"'
        ]
        encode = "Shift-JIS"
        if options.get('encoding'):
            encode = options.get('encoding')
        for line in data:
            if line == b"":
                continue
            new_line = b'"%s",' % (youki_kensa.name.encode(encode)) + line
            new_data.append(new_line)
        self.file = b"\n".join(new_data)

    def transform_propane_file(self, options, parent_context={}):
        propane_sales_header = self._get_ifdb_file_header(parent_context)
        data = self.file.split(b"\n")
        new_data = [
            b'"propane_sales_header_id","external_data_type","customer_branch_code",' + \
            b'"customer_branch_sub_code","customer_business_partner_code",' + \
            b'"customer_business_partner_branch_code","customer_delivery_code",' + \
            b'"direct_branch_code","direct_branch_sub_code","direct_business_partner_code",' + \
            b'"direct_business_partner_sub_code","direct_delivery_code","customer_name",' + \
            b'"codeommercial_branch_code","codeommercial_branch_sub_code",' + \
            b'"codeommercial_product_code","product_name","standard_name","standard",' + \
            b'"number","slip_date","codelassification_code","line_break","quantity",' + \
            b'"unit_code","unit_price","amount_of_money","unit_price_2","amount_2",' + \
            b'"unified_quantity","order_number","comment","codeommercial_branch_code2",' + \
            b'"codeommercial_branch_sub_code2","codeommercial_product_code2",' + \
            b'"amount_calculation_classification","slip_processing_classification"'
        ]
        encode = "Shift-JIS"
        if options.get('encoding'):
            encode = options.get('encoding')
        for line in data:
            if line == b"":
                continue
            new_line = b'"%s",' % (propane_sales_header.name.encode(encode)) + line
            new_data.append(new_line)
        self.file = b"\n".join(new_data)

    def _transform_ifdb_yg(self, data, header_id):
        def _ymd(short_dt):
            # convert 210203 to 20210203
            dt = short_dt.strip()
            if len(dt) != 6:
                return ''
            else:
                return '-'.join(['20' + dt[:2], dt[2:4], dt[4:]])

        FIELDS_BEFORE = FIELDS_MODEL[self.res_model]['FIELDS_BEFORE']
        FIELDS_AFTER = FIELDS_MODEL[self.res_model]['FIELDS_AFTER']
        # convert data to df
        df = pd.DataFrame(data, columns=FIELDS_BEFORE, dtype=object).fillna('').astype(str)
        for c in df.columns:
            df[c] = df[c].str.strip()

        # get data for transform
        external_data_types = list(df['customer_cd'])
        name_col = []
        for el in external_data_types:
            if len(name_col) == len(external_data_types):
                break
            name_col.append(str(header_id))
        df['header_id/ Database ID'] = name_col
        df['item'] = df['item']
        df['customer_cd'] = df['customer_cd']
        df['meter_reading_date'] = df['meter_reading_date']
        df['amount_use'] = df['amount_use']

        # sort
        df_sorted = df.reset_index(drop=True)

        # replace duplicated values
        # header_cols = [c for c in FIELDS_AFTER if not c.startswith('summary_ids')]
        # df_sorted.loc[df_sorted.duplicated(subset=['id']), header_cols] = ''
        return df_sorted[FIELDS_AFTER]

    def _transform_ifdb_yg_summary(self, data, header_id):
        def _ymd(short_dt):
            # convert 210203 to 20210203
            dt = short_dt.strip()
            if len(dt) != 6:
                return ''
            else:
                return '-'.join(['20' + dt[:2], dt[2:4], dt[4:]])

        FIELDS_BEFORE = FIELDS_MODEL[self.res_model]['FIELDS_BEFORE']
        FIELDS_AFTER = FIELDS_MODEL[self.res_model]['FIELDS_AFTER']
        # convert data to df
        df = pd.DataFrame(data, columns=FIELDS_BEFORE, dtype=object).fillna('').astype(str)
        for c in df.columns:
            df[c] = df[c].str.strip()

        # get data for transform
        external_data_types = list(df['partner_id'])
        name_col = []
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        upload_date_col = [now]
        for el in external_data_types:
            if len(name_col) == len(external_data_types):
                break
            name_col.append(str(header_id))
            upload_date_col.append('')
        df['header_id/ Database ID'] = name_col
        df['partner_id'] = df['partner_id']
        df['amount_use'] = df['amount_use']
        df['item'] = df['item']
        # sort
        df_sorted = df.reset_index(drop=True)

        # replace duplicated values
        # header_cols = [c for c in FIELDS_AFTER if not c.startswith('summary_ids')]
        # df_sorted.loc[df_sorted.duplicated(subset=['id']), header_cols] = ''
        return df_sorted[FIELDS_AFTER]

    def _read_file(self, options):
        MODEL_NAMES = ['ss_erp.ifdb.yg.summary', 'ss_erp.ifdb.yg.detail', 'ss_erp.ifdb.powernet.sales.detail',
                       'ss_erp.ifdb.youki.kanri.detail', 'ss_erp.ifdb.autogas.file.data.rec',
                       'ss_erp.ifdb.propane.sales.detail', 'ss_erp.account.transfer.result.line',
                       'ss_erp.account.receipt.notification.line']
        if self.res_model in MODEL_NAMES:
            options['encoding'] = 'shift_jis'
        res = super(Import, self)._read_file(options)
        if options.get('custom_transform'):
            # header
            FIELDS_AFTER = FIELDS_MODEL[self.res_model]['FIELDS_AFTER']

            yield FIELDS_AFTER
            # body
            df_res_trans = res
            if self.res_model == 'ss_erp.ifdb.yg.summary':
                df_res_trans = self._transform_ifdb_yg_summary(res, options.get('header_id'))
            if self.res_model == 'ss_erp.ifdb.yg.detail':
                df_res_trans = self._transform_ifdb_yg(res, options.get('header_id'))
            for row in df_res_trans.itertuples(index=False, name=None):
                yield row
        else:
            # 標準
            for row in res:
                yield row

    def do(self, fields, columns, options, dryrun=False):
        if self.import_file_header_id and self.res_model == 'ss_erp.account.transfer.result.line':
            header_rec = self.env['ss_erp.account.transfer.result.header'].browse(self.import_file_header_id)
            data_header = self.x_header_account_transfer
            header_rec.data_class = data_header[:1]
            header_rec.type_code = data_header[1:3]
            header_rec.entruster_code = data_header[4:14]
            header_rec.entruster_name = data_header[14:54]
            header_rec.withdrawal_date = data_header[54:58]
            header_rec.bank_id = data_header[58:62]
            header_rec.bank_branch_number = data_header[77:80]
            acc_type_number = 'normal' if data_header[95:96] == '1' else 'checking'
            header_rec.acc_type = acc_type_number
            header_rec.acc_number = data_header[96:103]
        else:
            header_rec = self.env['ss_erp.account.receipt.notification.header'].browse(self.import_file_header_id)
            data_header = self.x_header_account_receipt
            header_rec.data_class = data_header[:1]
            header_rec.type_code = data_header[1:3]
            header_rec.create_date = data_header[4:14]
            header_rec.acc_from_date = data_header[14:54]
            header_rec.acc_to_date = data_header[54:58]
            header_rec.bank_id = data_header[58:62]
            header_rec.bank_branch_number = data_header[77:80]
            acc_type_number = 'normal' if data_header[95:96] == '1' else 'checking'
            header_rec.acc_type = acc_type_number
            header_rec.acc_number = data_header[96:103]
            header_rec.acc_name = data_header[103:110]

        return super(Import, self).do(fields, columns, options, dryrun=dryrun)

    def transform_account_transfer_file(self, options, parent_context={}):

        transfer_header_id = self.env['ss_erp.account.transfer.result.header'].browse(
            parent_context['default_account_transfer_result_header_id'])
        self.import_file_header_id = parent_context['default_account_transfer_result_header_id']
        data = self.file.decode('shift-jis').split('\r\n')
        if not data[0].startswith('1'):
            raise UserError(
                _("データファイルをリロードしてください!")
            )
        # Todo Confirm dummy
        new_data = [
            b'"account_transfer_result_header_id","withdrawal_bank_number","withdrawal_bank_name",' + \
            b'"withdrawal_branch_number","withdrawal_branch_name",' + \
            b'"dummy1","deposit_type",' + \
            b'"account_number","depositor_name","withdrawal_amount",' + \
            b'"new_code","customer_number","transfer_result_code",' + \
            b'"dummy2"'
        ]

        encode = "Shift-JIS"
        self.x_header_account_transfer = str(data[0])
        body_data = data[1:-2]
        line = []
        for bd in body_data:
            name_header = '\n' + str(transfer_header_id.name) + ','
            line.append(name_header.encode(encode))

            withdrawal_bank_number = (bd[1:5]) + ','
            line.append(withdrawal_bank_number.encode(encode))

            withdrawal_bank_name = (bd[5:20]) + ','
            line.append(withdrawal_bank_name.encode(encode))

            withdrawal_branch_number = (bd[20:23]) + ','
            line.append(withdrawal_branch_number.encode(encode))

            withdrawal_branch_name = (bd[23:38]) + ','
            line.append(withdrawal_branch_name.encode(encode))

            dummy1 = (bd[38:42]) + ','
            line.append(dummy1.encode(encode))

            deposit_code = (bd[42:43])
            # deposit_type = 'normal' if deposit_code == '1' else 'checking'
            line.append(deposit_code.encode(encode))

            account_number = ',' + (bd[43:50]) + ','
            line.append(account_number.encode(encode))

            deposit_name = (bd[50:80]) + ','
            line.append(deposit_name.encode(encode))

            withdrawal_amount = (bd[80:90]) + ','
            line.append(withdrawal_amount.encode(encode))

            new_code = (bd[90:91])
            if new_code == '0':
                string_new_code = 'その他'
            elif new_code == '1':
                string_new_code = '第1回引落分'
            else:
                string_new_code = '変更分'
            line.append(string_new_code.encode(encode))

            customer_number = ',' + (bd[91:111]) + ','
            line.append(customer_number.encode(encode))

            transfer_result_code = (bd[111:112]) + ','
            line.append(transfer_result_code.encode(encode))

            dummy2 = (bd[112:120]) + ','
            line.append(dummy2.encode(encode))

            new_data += line
            line = []
        self.file = b"".join(new_data)


    def transform_account_receipt_file(self, options, parent_context={}):
        def _ymd(short_dt):
            # convert 210203 to 20210203
            dt = short_dt.strip()
            if len(dt) != 6:
                return ''
            else:
                return '-'.join(['20' + dt[:2], dt[2:4], dt[4:]])
        transfer_receipt_header_id = self.env['ss_erp.account.receipt.notification.header'].browse(
            parent_context['default_account_receipt_result_header_id'])
        self.import_file_header_id = parent_context['default_account_receipt_result_header_id']
        data = self.file.decode('shift-jis').split('\r\n')
        if not data[0].startswith('1'):
            raise UserError(
                _("データファイルをリロードしてください!")
            )
        # Todo Confirm dummy
        new_data = [
            b'"account_receipt_notification_header_id","reference_number","account_date",' + \
            b'"starting_date","transfer_amount",' + \
            b'"other_ticket_amount","transfer_client_code",' + \
            b'"transfer_client_name","bank_name","bank_branch_name",' + \
            b'"cancel_code","edi_information","dummy"'
        ]

        encode = "Shift-JIS"
        self.x_header_account_receipt = str(data[0])
        body_data = data[1:-2]
        line = []
        for bd in body_data:
            name_header = '\n' + str(transfer_receipt_header_id.name) + ','
            line.append(name_header.encode(encode))

            reference_number = (bd[1:7]) + ','
            line.append(reference_number.encode(encode))

            account_date = (bd[7:13]) + ','
            line.append(account_date.encode(encode))

            starting_date = (bd[13:19]) + ','
            line.append(starting_date.encode(encode))

            transfer_amount = (bd[19:29]) + ','
            line.append(transfer_amount.encode(encode))

            other_ticket_amount = (bd[29:39]) + ','
            line.append(other_ticket_amount.encode(encode))

            transfer_client_code = (bd[39:49]) + ','
            line.append(transfer_client_code.encode(encode))

            transfer_client_name = (bd[49:97]) + ','
            line.append(transfer_client_name.encode(encode))

            bank_name = (bd[97:112]) + ','
            line.append(bank_name.encode(encode))

            bank_branch_name = (bd[112:127]) + ','
            line.append(bank_branch_name.encode(encode))

            cancel_code = (bd[127:128])
            line.append(cancel_code.encode(encode))

            edi_information = (bd[128:148]) + ','
            line.append(edi_information.encode(encode))

            dummy = (bd[148:200]) + ','
            line.append(dummy.encode(encode))

            new_data += line
            line = []
        self.file = b"".join(new_data)
