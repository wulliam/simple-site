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
from simplesite.controllers.nav import NewNavForm, ValidBefore
from authkit.authorize.pylons_adaptors import authorize
from authkit.authenticate.form import Form

log = logging.getLogger(__name__)

class UniqueSectionPath(formencode.validators.FancyValidator):
    def _to_python(self, values, state):
        nav_q = meta.Session.query(model.Nav)
        query = nav_q.filter_by(section=values['section'],
            type='section', path=values['path'])
        if request.urlvars['action'] == 'save':
            query = query.filter(model.Nav.id != int(request.urlvars['id']))
        existing = query.first()
        if existing:
            raise formencode.Invalid('There is already a section in this'
                'section with this path', values, state)
        return values

class ValidSectionPosition(formencode.FancyValidator):
    def _to_python(self, values, state):
        nav_q = meta.Session.query(model.Nav)
        if values.get('type', 'section') == 'section':
            section = nav_q.filter_by(id = (values['section']))
            current_section = nav_q.filter_by(id = request.urlvars['id']).one()
            while section:
                if section.id == current_section.id:
                    raise formencode.Invalid('You can not move a section to'
                        'one of its subsections', values, state)
                if section.section == 1:
                    break
                section = nav_q.filter_by(id=section.section).first()
        return values               

class NewSectionForm(NewNavForm):
    chained_validators = [
        ValidBefore(),
        UniqueSectionPath(),
    ]

class EditSectionForm(NewNavForm):
    chained_validators = [
        ValidBefore(), 
        UniqueSectionPath(),
        ValidSectionPosition()
        ]

class SectionController(BaseController):

    def __before__(self, id=None):
        nav_q = meta.Session.query(model.Nav)
        if id:
            nav_q = nav_q.filter_by(type='section').filter(model.nav_table.c.id != int(id))
        else:
            nav_q = nav_q.filter_by(type='section')
        c.available_sections = [(nav.id, nav.name) for nav in nav_q]    
        log.info(str(c.available_sections))

    def index(self):
        # Return a rendered template
        #return render('/page.mako')
        # or, return a response
        return 'Hello World'
        
    def new(self):
        values = {}
        values.update(request.params)
        if values.has_key('before') and values['before'] == u'None':
            values['before'] = ''
        c.before_options = model.Nav.get_before_options(values.get('section', 0))
        c.before_options.append(['', '[At the end]'])
        return render('/derived/section/new.html')

    @restrict('POST')
    @validate(schema=NewSectionForm(), form='new')
    def create(self):
        section = model.Section()
        for k, v in self.form_result.items():
            setattr(section, k, v)
        meta.Session.add(section)
        model.Nav.add_navigation_node(section, self.form_result['section'],
            self.form_result['before'])
        meta.Session.commit()
        index_page = model.page()
        index_page.title = 'Section Index'
        index_page.name = 'Section Index'
        index_page.path = 'index'
        index_page.content = 'This is the index page for this section'
        meta.Session.add(index_page)
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='section', action='view', id=section.id)
        return "Moved temporarily"
    
    @authorize(h.auth.is_valid_user)    
    def edit(self, id=None):
        if id is None:
            abort(404)
        page_q = meta.Session.query(model.Section)
        section = page_q.filter_by(id=id).first()
        if section is None:
            abort(404)
        values = {
            'name': section.name,
            'path': section.path,
            'section': section.section,
            'before' : section.before,
        }
        c.before_options = model.Nav.get_before_options(section.section, section.id)
        c.before_options.append(['', '[At the end]'])
        return htmlfill.render(render('/derived/section/edit.html'), values)
    
    @authorize(h.auth.is_valid_user)     
    @restrict('POST')
    @validate(schema=EditSectionForm(), form='edit')
    def save(self, id=None):
        page_q = meta.Session.query(model.Section)
        section = page_q.filter_by(id=id).first()
        if section is None:
            abort(404)
        if not(section.section == self.form_result['section'] and \
            section.before == self.form_result['before']):
            model.Nav.remove_navigation_node(section)
            model.Nav.add_navigation_note(section, self.form_result['secction'],
                self.form.result['before'])
        for k,v in self.form_result.items():
            if getattr(section, k) != v:
                setattr(section, k, v)
        meta.Session.commit()
        session['flash']='Section successfully updated.'
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='section', action='view',
            id=section.id)
        return "Moved temporarily"
         
    def list(self):
        records = meta.Session.query(model.Section)
        c.paginator = paginate.Page(
            records,
            section = int(request.params.get('page',1)),
            items_per_page = 10,
            controller='section',
            action='list',
            )
        return render('/derived/section/list.html')
    
    @authorize(h.auth.has_delete_role)         
    def delete(self, id=None):
        if id is None:
            abort(404)
        section_q = meta.Session.query(model.Section)
        section = section_q.filter_by(id=id).first()
        if section is None:
            abort(404)
        nav_q = meta.Session.query(model.Nav)
        existing = nav_q.filter_by(section=id, type='section').filter(model.Page.path != 'index').first()
        if existing is None:
            return render('/derived/section/cannot_delete.html')
        index_page = nav_q.filter_by(section=id, type='section', path='index').first()
        if inex_page is not None:
            model.Nav.remove_navigation_node(index_page)
            meta.Session.delete(index_page)
        model.Nav.remove_navigation_node(section)
        meta.Session.delete(section)
        meta.Session.commit()
        return render('/derived/section/deleted.html')      
