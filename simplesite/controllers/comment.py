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

log = logging.getLogger(__name__)

class NewCommentForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = formencode.validators.String(not_empty=True)
    email = formencode.validators.Email(not_empty=True)
    content = formencode.validators.String(
        not_empty=True,
        messages={
            'empty':'Please enter a comment.'
        }
    )

class CommentController(BaseController):

    def __before__(self, action, pageid=None):
        log.info("page id %s".format(pageid))
        page_q = meta.Session.query(model.Page)
        c.page = pageid and page_q.filter_by(id=int(pageid)).first() or None
        if c.page is None:
            abort(404)

    def index(self):
        # Return a rendered template
        #return render('/page.mako')
        # or, return a response
        return 'Hello World'
        
    def view(self, id):
        if id is None:
            abort(404)
        page_q = model.meta.Session.query(model.Comment)
        c.comment = page_q.filter_by(pageid=c.page.id, id=int(id)).first()
        if c.comment is None:
            abort(404)
        return render('/derived/comment/view.html')
        
    def new(self):
        return render('/derived/comment/new.html')

    @restrict('POST')
    @validate(schema=NewCommentForm(), form='new')
    def create(self):
        log.info("create comment")
        comment = model.Comment()
        for k, v in self.form_result.items():
            log.info("%s,%s" % (k,v))
            setattr(comment, k, v)
        comment.pageid = c.page.id
        meta.Session.add(comment)
        meta.Session.commit()
        response.status_int = 302
        response.headers['location'] = h.url_for(pageid=c.page.id, controller='comment', action='view', id=comment.id)
        return "Moved temporarily"
        
    def edit(self, id=None):
        if id is None:
            abort(404)
        page_q = meta.Session.query(model.Comment)
        comment = page_q.filter_by(pageid=c.page.id, id=id).first()
        if comment is None:
            abort(404)
        values = {
            'name': comment.name,
            'email': comment.email,
            'content': comment.content
        }
        #c.title = comment.title
        return htmlfill.render(render('/derived/comment/edit.html'), values)
        
    @restrict('POST')
    @validate(schema=NewCommentForm(), form='edit')
    def save(self, id=None):
        page_q = meta.Session.query(model.Comment)
        comment = page_q.filter_by(id=id).first()
        if comment is None:
            abort(404)
        for k,v in self.form_result.items():
            if getattr(comment, k) != v:
                setattr(comment, k, v)
        meta.Session.commit()
        session['flash']='Comment successfully updated.'
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(pageid=c.page.id, controller='comment', action='view',
            id=comment.id)
        return "Moved temporarily"
         
    def list(self):
        comment_q = meta.Session.query(model.Comment).filter_by(pageid=c.page.id)
        comment_q = comment_q.order_by(model.comment_table.c.created.asc())
        c.paginator = paginate.Page(
            comment_q,
            comment = int(request.params.get('page',1)),
            items_per_page = 10,
            pageid = c.page.id,
            controller='comment',
            action='list',
            )
        return render('/derived/comment/list.html')
          
    def delete(self, id=None):
       if id is None:
           abort(404)
       page_q = meta.Session.query(model.Comment)
       comment = page_q.filter_by(pageid=c.page.id,id=id).first()
       meta.Session.delete(comment)
       meta.Session.commit()
       return render('/derived/comment/deleted.html')      
