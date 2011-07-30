"""Setup the SimpleSite application"""
import logging

from simplesite.config.environment import load_environment
from simplesite.model import meta
from simplesite import model

log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup simplesite here"""
    load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    meta.metadata.create_all(bind=meta.engine)

    log.info("Adding homepage...")
    page = model.Page()
    page.title=u'Home Page'
    page.content=u'Welcome to the SimpleSite home page'
    meta.Session.add(page)
    meta.Session.commit()
    log.info("Successfully setup.")
