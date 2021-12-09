from odoo import _, fields, models
from odoo.exceptions import UserError


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

    def transform_autogas_file(self, options, parent_context={}):
        self.ensure_one()
        autogas_header = False
        if parent_context and not any([self.import_file_header_id, self.import_file_header_model]):
            self.import_file_header_model = parent_context["default_import_file_header_model"]
            self.import_file_header_id = parent_context["default_import_file_header_id"]
            autogas_header = self.env[self.import_file_header_model].browse(
                self.import_file_header_id
            )
        if not autogas_header:
            raise UserError(_("Missing File Header, please using `upload` option from file header!"))
        data = self.file.decode("utf-8").split("\r\n")
        # remove the first and last line
        data = data[1:-2]
        new_data = [
            '"card_classification","processing_division","unused","group_division","actual_car_number","card_number","product_code","data_no","quantity_1","unit_price","amount_of_money","staff_code","processing_time","calendar_date","consumption_tax_output_classification","consumption_tax","credit_terminal_processing_serial_number","credit_classification","credit_data_no","tax_classification_code","filer1","quantity_2","filer2","autogas_file_header_id"'
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
        self.file = "\n".join(new_data).encode("utf-8")

    def transform_powernet_file(self, options, parent_context={}):
        self.ensure_one()
        powernet_header = False
        if parent_context and not any([self.import_file_header_id, self.import_file_header_model]):
            self.import_file_header_model = parent_context["default_import_file_header_model"]
            self.import_file_header_id = parent_context["default_import_file_header_id"]
            powernet_header = self.env[self.import_file_header_model].browse(
                self.import_file_header_id
            )
        if not powernet_header:
            raise UserError(_("Missing File Header, please using `upload` option from file header!"))
        data = self.file.split(b"\n")
        new_data = [
            '"powernet_sales_header_id","需要家コード","請求まとめコード","売上日","伝票種類","伝票Ｎｏ","データ種類","現金／掛け区分","商品コード","商品コード２","商品名","商品備考","売上区分","数量","単位コード","単価","金額","消費税","売上額","換算後数量","検索備考1","検索備考2","検索備考3","検索備考4","検索備考5","検索備考6","検索備考7","検索備考8","検索備考9","検索備考10","販売分類コード1","販売分類コード2","販売分類コード3","需要家販売分類コード1","需要家販売分類コード2","需要家販売分類コード3","需要家販売分類コード4","需要家販売分類コード5","商品分類コード1","商品分類コード2","商品分類コード3"'
        ]
        for line in data:
            if line == "":
                continue
            new_line = '"%s",' % (powernet_header.name.encode("utf-8")) + line
            new_data.append(new_line)
        self.file = "\n".join(new_data)
