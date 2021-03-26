# -*- coding: utf-8 -*-
import base64
import csv
import logging
import os
import shutil
import zipfile
from datetime import datetime
from io import BytesIO

from odoo import api, fields, models, tools, _
from odoo.exceptions import except_orm
from odoo.tools.osutil import tempdir

_logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 100 * 1024 * 1024  # in megabytes

addons_path = os.path.abspath(os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'static/src/img/'))


class ProductImageImport(models.TransientModel):
    _name = 'product.image.import'
    _description = 'Product Image Import'

    image_file = fields.Binary(string='.ZIP file', required=True)
    filename = fields.Char('File Name')

    def _write_bounced_images(self, file_head, bounced_detail, context):
        if not file_head:
            _logger.warning(
                "Can not Export bounced(Rejected) Images detail to the file. ")
            return False
        try:
            dtm = datetime.today().strftime("%Y%m%d%H%M%S")
            fname = "BOUNCED_IMAGES_"+dtm+".csv"
            _logger.info(
                "Opening file '%s' for logging the bounced images detail." % (fname))

            with open(file_head+"/"+fname, 'w', newline='') as csvfile:
                fl = csv.writer(csvfile, delimiter=' ',
                                quotechar=' ', quoting=csv.QUOTE_MINIMAL)
                for ln in bounced_detail:
                    fl.writerow(ln)
            _logger.info(
                "Successfully exported the bounced images detail to the file %s." % (fname))
            return {'file_path': file_head + "/" + fname, 'fname': fname}
        except Exception:
            _logger.warning(
                "Can not Export bounced(Rejected) images detail to the file. ")
            return False

    def load_images_from_folder(self):
        images = []
        zip_data = base64.decodestring(self.image_file)
        fp = BytesIO()
        fp.write(zip_data)
        path = self.import_zipfile(fp)
        bounced_image = []
        for filename in path:
            name = filename.split('/')[-1]
            try:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    with open(filename, 'rb') as fp:
                        image_base64 = base64.b64encode(fp.read())
                    images.append({'filename': name, 'default_code': name.split(
                        '.')[:1][0], 'image': image_base64})
                else:
                    if not filename.lower().endswith('/'):
                        bounced_image.append(
                            ["Images has no proper extension: " + str(name)])
            except Exception:
                bounced_image.append([str(name)])
        return images, bounced_image

    @api.model
    def import_zipfile(self, module_file):
        if not module_file:
            raise Exception(_("No file sent."))
        if not zipfile.is_zipfile(module_file):
            raise except_orm(_('Error!'), _('File is not a zip file!'))

        image_list = []
        with zipfile.ZipFile(module_file, "r") as z:
            for zn in z.namelist():
                image_list.append(addons_path + '/' + zn)
            for zf in z.filelist:
                if zf.file_size > MAX_FILE_SIZE:
                    raise except_orm(
                        _('Error!'), (_("File '%s' exceed maximum allowed file size") % zf.filename))
            with tempdir() as module_dir:
                import odoo.modules as addons
                try:
                    for root, dirs, files in os.walk(addons_path):
                        for f in files:
                            os.unlink(os.path.join(root, f))
                        for d in dirs:
                            shutil.rmtree(os.path.join(root, d))
                    addons.__path__.append(module_dir)
                    z.extractall(addons_path)
                finally:
                    addons.__path__.remove(module_dir)

        return image_list

    def confirm_import(self):
        images_data = self.load_images_from_folder()
        Product = self.env['product.product']
        bounce_imgs = images_data[1]

        for data in images_data[0]:
            prod_code = data['default_code']
            upper_code = prod_code.upper()
            upper_code = upper_code and upper_code.split('_')[0] or ''
            product_id = Product.search([('default_code', '=', upper_code)], limit=1)
            if not product_id and upper_code:
                product_id = Product.search(
                [('default_code', '=', 'DL-' + upper_code)], limit=1)
            if not product_id and upper_code:
                product_id = Product.search(
                [('default_code', '=', 'F-' + upper_code)], limit=1)
            if product_id and upper_code:
                image = tools.image_process(data['image'], size=(1024, 1024))
                product_id.image_1920 = image
            else:
                bounce_imgs.append(
                    ['Product(Item number) not found: ' + str(data['filename'])])

        ctx = {}
        if bounce_imgs:
            context = {}
            file = self._write_bounced_images('/tmp', bounce_imgs, context)
            f = open(file['file_path'])
            f.close()
            ctx.update({'default_is_bounced': True,
                        'default_file': file['file_path'].split("/")[-1]})

        _logger.info("Successfully completed import process.")
        return {
            'name': _('Notification'),
            'context': ctx,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'output.message',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class OutputMessage(models.TransientModel):
    _name = 'output.message'
    _description = "Output Message"

    is_bounced = fields.Boolean(default=False)
    file = fields.Char('File Location', size=128, readonly=True)
