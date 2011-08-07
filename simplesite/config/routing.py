"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper
from simplesite import model

def parse(environ, result):
    url = result.pop('url')
    try:
        environ['simplesite.navigation'] = navigation_from_path(url)
    except NoPage, e:
        result['controller'] = 'nav'
        result['action'] = 'nopage'
        result['section'] = e.section
        result['path'] = e.path
    except NoSection, e:
        result['controller'] = 'nav'
        result['action'] = 'nosection'
        result['section'] = e.section
        result['path'] = e.path
    except NotFound, e:
        #This cause the route to not match
        return False
    else:
        result['controller'] = 'page'
        result['action'] = 'view'
        result['id'] = environ['simplesite.navigation']['page'].id
        return True

def build(routing_variables):
    controller = routing_variables.get('controller')
    action = routing_variables.get('action')
    id = routing_variables.get('id')
    del routing_variables['id']
    routing_variables['url'] = model.Nav.nav_to_path(id)
    return routing_variables

class NoPage(Exception):
    pass

class NoSection(Exception):
    pass

class NotFound(Exception):
    pass

def navigation_from_path(path_info):
    result = {}
    nav_q = model.meta.Session.query(model.Nav)
    path_parts = path_info.split('/')
    result['breadcrumbs'] = []
    if path_info.endswith('/'):
        path_info += 'index'
    path_parts = path_info.split('/')
    for path in path_parts[:-1]:
        s = nav_q.filter_by(type='section', path=path).first()
        if s:
            result['breadcrumbs'].append(s)
        else:
            if path_info.endswith('/index') and \
                len(result['breadcrumbs']) == len(path_info.split('/'))-2:
                exception = NoSection('No section exists here')
                exception.section = result['breadcrumbs'][-1].id
                exception.path = path_parts[-2]
                raise exception
            else:
                raise NotFound('No section can be created here')
    result['page'] = nav_q.filter_by(type='page',
        section=result['breadcrumbs'][-1].id, path=path_parts[-1]).first()
    if result['page'] is None:
        if len(result['breadcrumbs']) == len(path_info.split('/'))-1:
            exception = NoPage('No page exists here')
            exception.section = result['breadcrumbs'][-1].id
            exception.path = path_parts[-1]
            raise exception
        else:
            raise NotFound('No page can be created here')
    result['breadcrumbs'].append(result['page'])
    # Add the path_info
    cur_path = ''
    for breadcrumb in result['breadcrumbs']:
        cur_path +=breadcrumb.path
        breadcrumb.path_info = cur_path
        if isinstance(breadcrumb, model.Section):
            breadcrumb.path_info = cur_path + '/'
            cur_path += '/'
    result['menu'] = menu(nav_q, result['breadcrumbs'][-2].id,
        result['breadcrumbs'][-2].path_info)
    result['tabs'] = menu(nav_q, result['breadcrumbs'][0].id,
        result['breadcrumbs'][0].path_info)
    return result

def menu(nav_q, sectionid, path_info):
    # There might also be child sections
    last = None
    navs = [nav for nav in nav_q.filter_by(section=sectionid).order_by(
        model.nav_table.c.before.desc()).all()]
    for nav in navs:
        if nav.before is None:
            # This is our last node
            last = nav
            break
    menu_dict = dict([[nav.before, nav] for nav in navs])
    if not last:
        raise Exception('No last node found')
    # Iterate over the nodes building them up in the correct order
    menu = [last]
    while len(menu) < len(navs):
        id = menu[0].id
        if not menu_dict.has_key(id):
            raise Exception("This section doesn't have an item %s to go "
                "before %r id %s"%(id, menu[0].name, menu[0].id))
        item = menu_dict[menu[0].id]
        menu.insert(0, item)
    f_menu = []
    for menu_item in menu:
        menu_item.path_info = path_info + menu_item.path
        if isinstance(menu_item, model.Section):
            menu_item.path_info += '/'
        elif menu_item.path_info.endswith('/index'):
            menu_item.path_info = menu_item.path_info[:-5]
        f_menu.append(menu_item)
    return f_menu

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'],explicit=True)
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    # CUSTOM ROUTES HERE
    
    map.connect('signout', '/signout', controller='account', action='signout')
    map.connect('signin', '/signin', controller='account', action='signin')
    map.connect('signinagain', '/signinagain', controller='account', action='signinagain')

    map.connect(
        '/page/{pageid}/{controller}/{action}',
        requirements=dict(pageid='\d+')
        )
    map.connect(
        '/page/{pageid}/{controller}/{action}/{id}',
        requirements=dict(pageid='\d+',id='\d+')
        )
    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')
    map.connect('path', '*url', conditions={'function':parse}, _filter=build)

    return map
