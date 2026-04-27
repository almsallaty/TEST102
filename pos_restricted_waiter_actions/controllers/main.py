import json

from odoo import http
from odoo.http import request


class PosRestrictedWaiterActionsController(http.Controller):

    @http.route('/pos_restricted_waiter_actions/log', type='http', auth='user', methods=['POST'], csrf=False)
    def pos_restricted_waiter_actions_log(self, **kwargs):
        payload = {}
        raw = request.httprequest.data or b'{}'
        try:
            payload = json.loads(raw.decode('utf-8'))
        except Exception:
            payload = {}
        request.env['pos.restricted.waiter.audit.log'].create_from_pos_payload(payload)
        return request.make_json_response({'ok': True})
