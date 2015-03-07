#!/usr/bin/python
# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) Vauxoo (<http://vauxoo.com>).
#    All Rights Reserved
# #############Credits#########################################################
#    Coded by: Humberto Arocha <hbto@vauxoo.com>
###############################################################################
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or (at your
#    option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
from openerp.osv import fields, osv
from openerp.addons.aging_due_report.report.parser import aging_parser as ag


class account_aging_wizard_document(osv.TransientModel):
    _name = 'account.aging.wizard.document'
    _rec_name = 'partner_id'
    _order = 'partner_id'

    _columns = {
        'partner_id': fields.many2one('res.partner', u'Partner'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
        'residual': fields.float('Residual'),
        'total': fields.float('Total'),
        'payment': fields.float('Payment'),
        'due_days': fields.float('Due Days'),
        'company_id': fields.many2one('res.company', u'Company'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'aaw_id': fields.many2one(
            'account.aging.wizard',
            'Account Aging Wizard',
            help='Account Aging Wizard Holder'),
    }


class account_aging_wizard_currency(osv.osv_memory):
    _name = 'account.aging.wizard.currency'
    _description = 'Price List'
    _rec_name = 'currency_id'
    _columns = {
        'currency_id': fields.many2one(
            'res.currency', 'Currency',
            required=True,),
        'aaw_id': fields.many2one(
            'account.aging.wizard',
            'Account Aging Wizard',
            help='Account Aging Wizard Holder'),
    }


class account_aging_partner_wizard(osv.osv_memory):
    _name = 'account.aging.wizard'
    _description = 'Price List'
    _rec_name = 'result_selection'

    _columns = {
        'report_format': fields.selection([
            ('pdf', 'PDF'),
            # TODO: enable print on controller to HTML
            # ('html', 'HTML'),
            ('xls', 'Spreadsheet')],
            'Report Format',
            required=True),
        'result_selection': fields.selection(
            [('customer', 'Receivable'),
             ('supplier', 'Payable')],
            "Target",
            required=True),
        'type': fields.selection(
            [('aging', 'Aging Report'),
             ('detail', 'Detailed Report'),
             ('formal', 'Formal Report')],
            "Type",
            required=True),
        'currency_ids': fields.one2many(
            'account.aging.wizard.currency',
            'aaw_id', 'Balance by Currency',
            help='Balance by Currency'),
        'document_ids': fields.one2many(
            'account.aging.wizard.document',
            'aaw_id', 'Balance by Currency',
            help='Balance by Currency'),
    }
    _defaults = {
        'report_format': lambda *args: 'xls',
        'result_selection': lambda *args: 'customer',
        'type': lambda *args: 'aging',
    }

    def compute_lines(self, cr, uid, ids, partner_ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        rp_obj = self.pool.get('res.partner')

        wzd_brw = self.browse(cr, uid, ids[0], context=context)
        rp_brws = rp_obj.browse(cr, uid, partner_ids, context=context)
        ag_obj = ag(cr, uid, None, context=context)
        rex = ag_obj._get_invoice_by_currency_group(rp_brws)
        res = []

        wzd_brw.document_ids.unlink()

        for itr in rex[0]:
            for key, val in itr.iteritems():
                if key == 'inv_ids':
                    import pdb; pdb.set_trace()
                    for each in val:
                        res.append(each)

        res = [(0, 0, line) for line in res]
        wzd_brw.write({'document_ids': res})
        return True

    def print_report(self, cr, uid, ids, context=None):
        """
        To get the date and print the report
        @return : return report
        """
        context = dict(context or {})
        ids = isinstance(ids, (int, long)) and [ids] or ids
        wzd_brw = self.browse(cr, uid, ids[0], context=context)

        self.compute_lines(cr, uid, ids, context.get('active_ids', []),
                           context=context)

        datas = {'active_ids': context.get('active_ids', [])}

        context['xls_report'] = wzd_brw.report_format == 'xls'
        name = 'aging_due_report.aging_due_report_qweb'
        if wzd_brw.result_selection == 'customer':
            if wzd_brw.type == 'aging':
                name = 'aging_due_report.aging_due_report_qweb'
            if wzd_brw.type == 'detail':
                name = 'aging_due_report.detail_due_report_qweb'
            if wzd_brw.type == 'formal':
                name = 'aging_due_report.formal_due_report_qweb'
        elif wzd_brw.result_selection == 'supplier':
            if wzd_brw.type == 'aging':
                name = 'aging_due_report.supplier_aging_due_report_qweb'
            if wzd_brw.type == 'detail':
                name = 'aging_due_report.supplier_detail_due_report_qweb'
            if wzd_brw.type == 'formal':
                name = 'aging_due_report.supplier_formal_due_report_qweb'

        return self.pool['report'].get_action(cr, uid, [], name, data=datas,
                                              context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
