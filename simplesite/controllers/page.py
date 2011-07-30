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

class NewPageForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    content = formencode.validators.String(
        not_empty=True,
        messages={
            'empty':'Please enter some content for the page.'
        }
    )
    heading = formencode.validators.String()
    title = formencode.validators.String(not_empty=True)

class ValidTags(formencode.FancyValidator):
    def _to_pyton(self, value, state):
        all_tag_ids = [tag.id for tag in meta.Session.query(model.Tag)]
        for tag_id in value['tags']:
            if tag_id not in all_tag_ids:
                raise forencode.Invalid(
                    "One or more selected tags could not be found in the database",
                    values,
                    state
                    )
        return values

class ValidTagsForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    tags = formencode.foreach.ForEach(formencode.validators.Int())
    chained_validators = [ValidTags()]

class PageController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/page.mako')
        # or, return a response
        return 'Hello World'
        
    @restrict('POST')
    @validate(schema=ValidTagsForm(), form='view')
    def update_tags(self, id=None):
        if id is None:
            abort(404)
        page_q = meta.Session.query(model.Page)
        page = page_q.filter_by(id=id).first()
        if page is None:
            abort(404)
        tag_to_add = []
        for i, tag in enumerate(page.tags):
            if tag.id not in self.form_result['tags']:
                del page.tags[i]
        tagids = [tag.id for tag in page.tags]
        for tag in self.form_result['tags']:
            if tag not in tagids:
                t = meta.Session.query(model.Tag).get(tag)
                page.tags.append(t)
        meta.Session.commit()
        session['flash'] = 'Tags successfully updated'
        session.save()
        return redirect_to(controller='page', action='view', id=page.id)

    def view(self, id):
        if id is None:
            abort(404)
        page_q = model.meta.Session.query(model.Page)
        c.page = page_q.get(int(id))
        c.comment_count = model.meta.Session.query(model.Comment).filter_by(pageid=id).count()
        if c.page is None:
            abort(404)
        tag_q = meta.Session.query(model.Tag)
        c.available_tags = [(tag.id, tag.name) for tag in tag_q]
        c.selected_tags = {'tags':[str(tag.id) for tag in c.page.tags]}
        return render('/derived/page/view.html')
        
    def new(self):
        return render('/derived/page/new.html')

    @restrict('POST')
    @validate(schema=NewPageForm(), form='new')
    def create(self):
        page = model.Page()
        for k, v in self.form_result.items():
            setattr(page, k, v)
        meta.Session.add(page)
        meta.Session.commit()
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='page', action='view', id=page.id)
        return "Moved temporarily"
        
    def edit(self, id=None):
        if id is None:
            abort(404)
        page_q = meta.Session.query(model.Page)
        page = page_q.filter_by(id=id).first()
        if page is None:
            abort(404)
        values = {
            'title': page.title,
            'heading': page.heading,
            'content': page.content
        }
        c.title = page.title
        return htmlfill.render(render('/derived/page/edit.html'), values)
        
    @restrict('POST')
    @validate(schema=NewPageForm(), form='edit')
    def save(self, id=None):
        page_q = meta.Session.query(model.Page)
        page = page_q.filter_by(id=id).first()
        if page is None:
            abort(404)
        for k,v in self.form_result.items():
            if getattr(page, k) != v:
                setattr(page, k, v)
        meta.Session.commit()
        session['flash']='Page successfully updated.'
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='page', action='view',
            id=page.id)
        return "Moved temporarily"
         
    def list(self):
        records = meta.Session.query(model.Page)
        c.paginator = paginate.Page(
            records,
            page = int(request.params.get('page',1)),
            items_per_page = 10,
            controller='page',
            action='list',
            )
        return render('/derived/page/list.html')
          
    def delete(self, id=None):
       if id is None:
           abort(404)
       page_q = meta.Session.query(model.Page)
       page = page_q.filter_by(id=id).first()
       meta.Session.delete(page)
       meta.Session.execute(delete(model.pagetag_table, model.pagetag_table.c.pageid==page.id))
       meta.Session.commit()
       return render('/derived/page/deleted.html')      
