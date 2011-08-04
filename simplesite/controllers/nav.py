import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from simplesite.lib.base import BaseController, render
from simplesite.model import meta
from simplesite import model
import formencode


log = logging.getLogger(__name__)

class ValidBefore(formencode.FancyValidator):
    def _to_python(self, values, state):
        nav_q = meta.Session.query(model.Nav)
        if values.get('before'):
            valid_ids = [nav.id for nav in nav_q.filter_by(
                section = values['section']).all()]
            if int(values['before']) not in valid_ids:
                raise formencode.Invalid("Please check the section "
                    "and before values", values, state)
        return values

class NewNavForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = formencode.validators.String(not_empty=True)
    path = formencode.validators.Regex(not_empty=True, regex='^[a-zA-Z0-9_-]+$')
    section = formencode.validators.Int(not_empty=True)
    before = formencode.validators.Int()
    chained_validators = [ValidBefore()]

class NavController(BaseController):

    def nopage(self, section, path):
        return render('/derived/nav/create_page.html')

    def nosection(self, section, path):
        return render('/derived/nav/create_section.html')

