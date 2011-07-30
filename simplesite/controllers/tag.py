import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from simplesite import model

from simplesite.lib.base import BaseController, render
import formencode
from formencode import htmlfill
from pylons.decorators.rest import restrict
from pylons import session
from pylons.decorators import validate
from simplesite.model import meta
import simplesite.lib.helpers as h
import webhelpers.paginate as paginate
from sqlalchemy import delete

log = logging.getLogger(__name__)

import re

class UniqueTag(formencode.validators.FancyValidator):
    def to_python(self, value, state):
        #check we have a valid string first
        value = formencode.validators.String(max=20).to_python(value, state)
        #check that tags are only letters, numbers, and the space character
        result = re.compile("[^a-zA-Z0-9 ]").search(value)
        if result:
            formencode.Invalid("Tags can only contain letters, numbers and spaces", value, state)
        tag_q = meta.Session.query(model.Tag).filter_by(name=value)
        if request.urlvars['action'] == 'save':
            #Ignore the exsiting name when performing the check
            tag_q = tag_q.filter(model.Tag.id != int(request.urlvars['id']))
        first_tag = tag_q.first()
        if first_tag is not None:
            raise formencode.Invalid("This tag name already existed", value, state)
        return value

class NewTagForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = formencode.validators.String(not_empty=True)
    name = UniqueTag(not_empty=True)


class TagController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/page.mako')
        # or, return a response
        return 'Hello World'
        
    def view(self, id):
        if id is None:
            abort(404)
        page_q = model.meta.Session.query(model.Tag)
        c.tag = page_q.get(int(id))
        if c.tag is None:
            abort(404)
        return render('/derived/tag/view.html')
        
    def new(self):
        return render('/derived/tag/new.html')

    @restrict('POST')
    @validate(schema=NewTagForm(), form='new')
    def create(self):
        tag = model.Tag()
        for k, v in self.form_result.items():
            setattr(tag, k, v)
        meta.Session.add(tag)
        meta.Session.commit()
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='tag', action='view', id=tag.id)
        return "Moved temporarily"
        
    def edit(self, id=None):
        if id is None:
            abort(404)
        page_q = meta.Session.query(model.Tag)
        tag = page_q.filter_by(id=id).first()
        if tag is None:
            abort(404)
        values = {
            'name': tag.name,
        }
        return htmlfill.render(render('/derived/tag/edit.html'), values)
        
    @restrict('POST')
    @validate(schema=NewTagForm(), form='edit')
    def save(self, id=None):
        page_q = meta.Session.query(model.Tag)
        tag = page_q.filter_by(id=id).first()
        if tag is None:
            abort(404)
        for k,v in self.form_result.items():
            if getattr(tag, k) != v:
                setattr(tag, k, v)
        meta.Session.commit()
        session['flash']='Tag successfully updated.'
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='tag', action='view',
            id=tag.id)
        return "Moved temporarily"
         
    def list(self):
        records = meta.Session.query(model.Tag)
        c.paginator = paginate.Page(
            records,
            tag = int(request.params.get('page',1)),
            items_per_page = 10,
            controller='tag',
            action='list',
            )
        return render('/derived/tag/list.html')
          
    def delete(self, id=None):
       if id is None:
           abort(404)
       page_q = meta.Session.query(model.Tag)
       tag = page_q.filter_by(id=id).first()
       meta.Session.delete(tag)
       meta.Session.delete(delete(model.pagetag_table, model.pagetag_table.c.tagid==tag.id))
       meta.Session.commit()
       return render('/derived/tag/deleted.html')      
