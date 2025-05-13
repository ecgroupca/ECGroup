# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class DeliveryCarrier(models.Model):
    """Inherit the model to handle the delivery carrier in the connector"""
    _inherit = "delivery.carrier"

    shopify_code = fields.Char("Shopify Delivery Code")
    shopify_source = fields.Char("Shopify Delivery Source")
    shopify_tracking_company = fields.Selection([
        ('4PX', '4PX'),
        ('APC', 'APC'),
        ('Amazon Logistics UK', 'Amazon Logistics UK'),
        ('Amazon Logistics US', 'Amazon Logistics US'),
        ('Anjun Logistics', 'Anjun Logistics'),
        ('Australia Post', 'Australia Post'),
        ('Bluedart', 'Bluedart'),
        ('Canada Post', 'Canada Post'),
        ('Canpar', 'Canpar'),
        ('China Post', 'China Post'),
        ('Chukou1', 'Chukou1'),
        ('Correios', 'Correios'),
        ('Couriers Please', 'Couriers Please'),
        ('DHL Express', 'DHL Express'),
        ('DHL eCommerce', 'DHL eCommerce'),
        ('DHL eCommerce Asia', 'DHL eCommerce Asia'),
        ('DPD', 'DPD'),
        ('DPD Local', 'DPD Local'),
        ('DPD UK', 'DPD UK'),
        ('Delhivery', 'Delhivery'),
        ('Eagle', 'Eagle'),
        ('FSC', 'FSC'),
        ('Fastway Australia', 'Fastway Australia'),
        ('FedEx', 'FedEx'),
        ('GLS', 'GLS'),
        ('GLS (US)', 'GLS (US)'),
        ('Globegistics', 'Globegistics'),
        ('Japan Post (EN)', 'Japan Post (EN)'),
        ('Japan Post (JA)', 'Japan Post (JA)'),
        ('La Poste', 'La Poste'),
        ('New Zealand Post', 'New Zealand Post'),
        ('Newgistics', 'Newgistics'),
        ('PostNL', 'PostNL'),
        ('PostNord', 'PostNord'),
        ('Purolator', 'Purolator'),
        ('Royal Mail', 'Royal Mail'),
        ('SF Express', 'SF Express'),
        ('SFC Fulfillment', 'SFC Fulfillment'),
        ('Sagawa (EN)', 'Sagawa (EN)'),
        ('Sagawa (JA)', 'Sagawa (JA)'),
        ('Sendle', 'Sendle'),
        ('Singapore Post', 'Singapore Post'),
        ('StarTrack', 'StarTrack'),
        ('TNT', 'TNT'),
        ('Toll IPEC', 'Toll IPEC'),
        ('UPS', 'UPS'),
        ('USPS', 'USPS'),
        ('Whistl', 'Whistl'),
        ('Yamato (EN)', 'Yamato (EN)'),
        ('Yamato (JA)', 'Yamato (JA)'),
        ('YunExpress', 'YunExpress'),
        ('AGS', 'AGS'),
        ('An Post', 'An Post'),
        ('Asendia USA', 'Asendia USA'),
        ('Bonshaw', 'Bonshaw'),
        ('BPost', 'BPost'),
        ('BPost International', 'BPost International'),
        ('BPost International', 'BPost International'),
        ('CDL Last Mile', 'CDL Last Mile'),
        ('Chronopost', 'Chronopost'),
        ('Colissimo', 'Colissimo'),
        ('Comingle', 'Comingle'),
        ('Coordinadora', 'Coordinadora'),
        ('Correos', 'Correos'),
        ('CTT', 'CTT'),
        ('CTT Express', 'CTT Express'),
        ('Cyprus Post', 'Cyprus Post'),
        ('Delnext', 'Delnext'),
        ('Deutsche Post', 'Deutsche Post'),
        ('DTD Express', 'DTD Express'),
        ('DX', 'DX'),
        ('Estes', 'Estes'),
        ('Evri', 'Evri'),
        ('First Global Logistics', 'First Global Logistics'),
        ('First Line', 'First Line'),
        ('Fulfilla', 'Fulfilla'),
        ('Guangdong Weisuyi Information Technology (WSE)', 'Guangdong Weisuyi Information Technology (WSE)'),
        ('Heppner Internationale Spedition GmbH & Co.', 'Heppner Internationale Spedition GmbH & Co.'),
        ('Iceland Post', 'Iceland Post'),
        ('IDEX', 'IDEX'),
        ('Israel Post', 'Israel Post'),
        ('Lasership', 'Lasership'),
        ('Latvia Post', 'Latvia Post'),
        ('Lietuvos Paštas', 'Lietuvos Paštas'),
        ('Logisters', 'Logisters'),
        ('Lone Star Overnight', 'Lone Star Overnight'),
        ('M3 Logistics', 'M3 Logistics'),
        ('Meteor Space', 'Meteor Space'),
        ('Mondial Relay', 'Mondial Relay'),
        ('NinjaVan', 'NinjaVan'),
        ('North Russia Supply Chain (Shenzhen) Co.', 'North Russia Supply Chain (Shenzhen) Co.'),
        ('OnTrac', 'OnTrac'),
        ('Packeta', 'Packeta'),
        ('Pago Logistics', 'Pago Logistics'),
        ('Ping An Da Tengfei Express', 'Ping An Da Tengfei Express'),
        ('Pitney Bowes', 'Pitney Bowes'),
        ('Portal PostNord', 'Portal PostNord'),
        ('Poste Italiane', 'Poste Italiane'),
        ('PostNord DK', 'PostNord DK'),
        ('PostNord NO', 'PostNord NO'),
        ('PostNord SE', 'PostNord SE'),
        ('Qxpress', 'Qxpress'),
        ('Qyun Express', 'Qyun Express'),
        ('Royal Shipments', 'Royal Shipments'),
        ('SHREE NANDAN COURIER', 'SHREE NANDAN COURIER'),
        ('Southwest Air Cargo', 'Southwest Air Cargo'),
        ('Step Forward Freight', 'Step Forward Freight'),
        ('Swiss Post', 'Swiss Post'),
        ('TForce Final Mile', 'TForce Final Mile'),
        ('Tinghao', 'Tinghao'),
        ('United Delivery Service', 'United Delivery Service'),
        ('Venipak', 'Venipak'),
        ('We Post', 'We Post'),
        ('Wizmo', 'Wizmo'),
        ('WMYC', 'WMYC'),
        ('Xpedigo', 'Xpedigo'),
        ('XPO Logistics', 'XPO Logistics'),
        ('YiFan Express', 'YiFan Express'),
        ('Aramex Australia', 'Aramex Australia'),
        ('TNT Australia', 'TNT Australia'),
        ('Hunter Express', 'Hunter Express'),
        ('Bonds', 'Bonds'),
        ('Allied Express', 'Allied Express'),
        ('Direct Couriers', 'Direct Couriers'),
        ('Northline', 'Northline'),
        ('GO Logistics', 'GO Logistics'),
        ('Österreichische Post', 'Österreichische Post'),
        ('Speedy', 'Speedy'),
        ('Intelcom', 'Intelcom'),
        ('BoxKnight', 'BoxKnight'),
        ('Loomis', 'Loomis'),
        ('WanbExpress', 'WanbExpress'),
        ('Zásilkovna', 'Zásilkovna'),
        ('Deutsche Post (DE)', 'Deutsche Post (DE)'),
        ('Deutsche Post (EN)', 'Deutsche Post (EN)'),
        ('DHL', 'DHL'),
        ('Swiship', 'Swiship'),
        ('Hermes', 'Hermes'),
        ('SEUR', 'SEUR'),
        ('Colissimo', 'Colissimo'),
        ('Mondial Relay', 'Mondial Relay'),
        ('Colis Privé', 'Colis Privé'),
        ('Evri', 'Evri'),
        ('Parcelforce', 'Parcelforce'),
        ('Yodel', 'Yodel'),
        ('DHL Parcel', 'DHL Parcel'),
        ('Tuffnells', 'Tuffnells'),
        ('ACS Courier', 'ACS Courier'),
        ('Fastway', 'Fastway'),
        ('DPD Ireland', 'DPD Ireland'),
        ('DTDC', 'DTDC'),
        ('India Post', 'India Post'),
        ('Gati KWE', 'Gati KWE'),
        ('Professional Couriers', 'Professional Couriers'),
        ('XpressBees', 'XpressBees'),
        ('Ecom Express', 'Ecom Express'),
        ('Ekart', 'Ekart'),
        ('Shadowfax', 'Shadowfax'),
        ('BRT', 'BRT'),
        ('GLS Italy', 'GLS Italy'),
        ('DHL Parcel', 'DHL Parcel'),
        ('Bring', 'Bring'),
        ('Inpost', 'Inpost'),
        ('PTT', 'PTT'),
        ('Yurtiçi Kargo', 'Yurtiçi Kargo'),
        ('Aras Kargo', 'Aras Kargo'),
        ('Sürat Kargo', 'Sürat Kargo'),
        ('Alliance Air Freight', 'Alliance Air Freight'),
        ('Pilot Freight', 'Pilot Freight'),
        ('LSO', 'LSO'),
        ('Old Dominion', 'Old Dominion'),
        ('R+L Carriers', 'R+L Carriers'),
        ('Southwest Air Cargo', 'Southwest Air Cargo'),
        ('Fastway', 'Fastway'),
        ('Skynet', 'Skynet'),
        ('Italy BTR', 'Italy BTR'),
    ], help="shopify_tracking_company selection help:When creating a fulfillment for a supported carrier, send the"
            "tracking_company exactly as written in the list above. If the tracking company doesn't match one of the"
            "supported entries, then the shipping status might not be updated properly during the fulfillment process.")

    def shopify_search_create_delivery_carrier(self, line, instance):
        """
        This method use to search and create delivery carrier base on received response in order line.
        :param line: Response of order line as received from Shopify store.
        :param instance: Response of instance.
        :return: carrier
        """
        delivery_source = line.get('source')
        delivery_code = line.get('code')
        delivery_title = line.get('title')
        carrier = self.env['delivery.carrier']
        if delivery_source and delivery_code:
            carrier = self.search([('shopify_source', '=', delivery_source), '|', ('shopify_code', '=', delivery_code),
                                   ('shopify_tracking_company', '=', delivery_code),
                                   ('company_id', 'in', [instance.shopify_company_id.id, False])], limit=1)

            if not carrier:
                carrier = self.search(
                    [('name', '=', delivery_title), ('company_id', 'in', [instance.shopify_company_id.id, False])],
                    limit=1)
                if carrier:
                    carrier.write({'shopify_source': delivery_source, 'shopify_code': delivery_code})

            if not carrier:
                carrier = self.create(
                    {'name': delivery_title, 'shopify_code': delivery_code, 'shopify_source': delivery_source,
                     'product_id': instance.shipping_product_id.id, 'company_id': instance.shopify_company_id.id})
        return carrier

    def search_carrier_for_webhook_fulfillment(self, instance, fulfillment_data):
        """
        This method is use to search the carrier for webhook fulfillment
        """
        carrier_company = fulfillment_data.get('tracking_company')
        if carrier_company:
            carrier = self.search([('shopify_tracking_company', '=', carrier_company)], limit=1)
            if carrier:
                return carrier
        carrier_name = fulfillment_data.get('service')
        carrier = False
        if carrier_name:
            carrier = self.search([('name', '=', carrier_name)], limit=1)
            if not carrier:
                carrier = self.create(
                    {'name': carrier_name, 'shopify_code': carrier_name, 'shopify_source': carrier_name,'product_id': instance.shipping_product_id.id})
        return carrier
