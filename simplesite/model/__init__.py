"""The application's model objects"""
import sqlalchemy as sa
from sqlalchemy import orm

from simplesite.model import meta

import datetime
from sqlalchemy import schema, types

def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    ## Reflected tables must be defined and mapped here
    #global reflected_table
    #reflected_table = sa.Table("Reflected", meta.metadata, autoload=True,
    #                           autoload_with=engine)
    #orm.mapper(Reflected, reflected_table)
    #
    meta.Session.configure(bind=engine)
    meta.engine = engine


## Non-reflected tables may be defined and mapped at module level
#foo_table = sa.Table("Foo", meta.metadata,
#    sa.Column("id", sa.types.Integer, primary_key=True),
#    sa.Column("bar", sa.types.String(255), nullable=False),
#    )
#
#class Foo(object):
#    pass
#
#orm.mapper(Foo, foo_table)


## Classes for reflected tables may be defined here, but the table and
## mapping itself must be done in the init_model function
#reflected_table = None
#
#class Reflected(object):
#    pass

def now():
    return datetime.datetime.now()

page_table = schema.Table('page', meta.metadata,
    schema.Column('id', types.Integer,
        schema.ForeignKey('nav.id'), primary_key=True),
    schema.Column('content', types.Text(), nullable=False),
    schema.Column('posted', types.DateTime(), default=now),
    schema.Column('title', types.Unicode(255), default=u'Untitled Page'),
    schema.Column('heading', types.Unicode(255)),
)

comment_table = schema.Table('comment', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('comment_seq_id', optional=True), primary_key=True),
    schema.Column('pageid', types.Integer,
        schema.ForeignKey('page.id'), nullable=False),
    schema.Column('content', types.Text(), default=u''),
    schema.Column('name', types.Unicode(255)),
    schema.Column('email', types.Unicode(255), nullable=False),
    schema.Column('created', types.TIMESTAMP(), default=now()),
)

pagetag_table = schema.Table('pagetag', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('pagetag_seq_id', optional=True), primary_key=True),
    schema.Column('pageid', types.Integer, schema.ForeignKey('page.id')),
    schema.Column('tagid', types.Integer, schema.ForeignKey('tag.id')),
)

tag_table = schema.Table('tag', meta.metadata,
    schema.Column('id', types.Integer,
        schema.Sequence('tag_seq_id', optional=True), primary_key=True),
    schema.Column('name', types.Unicode(20), nullable=False, unique=True),
)

nav_table = schema.Table('nav', meta.metadata,
    schema.Column('id', types.Integer(),
        schema.Sequence('nav_id_seq', optional=True), primary_key=True),
    schema.Column('name', types.Unicode(255), default=u'Untitled Node'),
    schema.Column('path', types.Unicode(255), default=u''),
    schema.Column('section', types.Integer(), schema.ForeignKey('nav.id')),
    schema.Column('before', types.Integer(), default=None),
    schema.Column('type', types.String(30), nullable=False)
    )

section_table = schema.Table('section', meta.metadata,
    schema.Column('id', types.Integer,
        schema.ForeignKey('nav.id'), primary_key = True),
   ) 

class Nav(object):
    @staticmethod
    def add_navigation_node(nav, section, before):
        nav_q = meta.Session.query(Nav)
        new_before = nav_q.filter_by(section=section, before=before).first()
        if new_before is not None and new_before_id != nav.id:
            new_before.before = nav.id

    @staticmethod
    def remove_navigation_node(nav):
        nav_q = meta.Session.query(Nav)
        old_before = nav_q.filter_by(section='section', before=nav.id).first()
        if old_before is not None:
            old_before.before = nav.before
            
    @staticmethod
    def nav_to_path(id):
        nav_q = meta.Session.query(Nav)
        nav = nav_q.filter_by(id=id).one()
        path = nav.path
        if nav.type=='section':
            path += '/'
        while nav.section is not None:
            nav = nav_q.filter_by(type='section', id=nav.section).one()
            path = nav.path+'/'+path
        return path
    

class Page(Nav):
    pass

class Section(Nav):
    pass

class Comment(object):
    pass

class Tag(object):
    pass

orm.mapper(Comment, comment_table)
orm.mapper(Tag, tag_table)
orm.mapper(Nav, nav_table, polymorphic_on = nav_table.c.type, polymorphic_identity='nav')
orm.mapper(Section, section_table, inherits=Nav, polymorphic_identity='section')
orm.mapper(Page, page_table, inherits=Nav, polymorphic_identity='page', properties={
   'comments':orm.relation(Comment, backref='page',cascade='all'),
   'tags':orm.relation(Tag, secondary=pagetag_table)
})

