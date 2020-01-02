#################
#### imports ####
#################
from __future__ import with_statement
from fabric.api import run, env, local, settings, abort, cd, prefix, sudo
from fabric.contrib.console import confirm
from contextlib import contextmanager as _contextmanager
from fabric.context_managers import shell_env
import os
import config

# Double tunnel
# http://stackoverflow.com/questions/6161548/fabric-how-to-double-tunnel

# Port is needed for gateway connections
# https://github.com/fabric/fabric/issues/884
# https://github.com/fabric/fabric/commit/d41e39b801320fde3ae2ae994ff78d57feb10959
PORT = 22

env.forward_agent = True
env.gateway = "%s@%s" % (config.GATEWAY_USERNAME, config.GATEWAY_SERVER)
env.hosts = ["%s@%s" % (config.USERNAME, config.SERVER)]
env.passwords = {
    "%s@%s:%s" % (config.GATEWAY_USERNAME, config.GATEWAY_SERVER, PORT): config.GATEWAY_PASSWORD,
    "%s@%s:%s" % (config.USERNAME, config.SERVER, PORT): config.PASSWORD
}


HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))

PROJECT_DIR = "/var/www/apps/project"
VIRTUAL_ENV = "%s/venv" % PROJECT_DIR
WSGI_SCRIPT = '%s/project.wsgi' % PROJECT_DIR

env.directory = PROJECT_DIR
env.activate = "source %s/bin/activate" % VIRTUAL_ENV


for host in env.hosts:
    print("Executing on %s" % (host))
#print("Executing on %s as %s" % (env.host, env.user))
#print("Executing on %(host)s as %(user)s" % env)


# $ fab hello
def hello():
    print("Hello world!")


# $ fab goodbye:name=Jeff
# $ fab goodbye:Jeff
def goodbye(name="world"):
    print("Bye %s!" % name)


# $ fab -H dazcona@gateway.computing.dcu.ie host_type
# $ fab -H dazcona@gateway.computing.dcu.ie --password XXXXXX host_type
def host_type():
    run('uname -s')


def whoami():
    run('whoami')


def sudo_whoami():
    with settings(sudo_user='root'):
        sudo("whoami") # prints 'root', password prompt bypassed
    with settings(sudo_user='david'):
        sudo("whoami") # prints 'david'


def hostname():
    run('hostname')


def echo():
    local("echo Hello World!")


def uptime():
    local("uptime")


def test():
    with settings(warn_only=True):
        cmd = "python manage.py test"
        print("Running: %s" % (cmd))
        result = local(cmd, capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")


def add_untracked_files():
    local("git add -A")


def commit():
    local("git add . && git commit")


def push():
    local("git push")


def prepare_deploy():
    print("Uploading code")
    print("Dir: %s" % (HERE))
    # You have to be under the project directory when you try to run this, otherwise it would fail with the message:
    # fatal: Not a git repository (or any of the parent directories): .git
    with cd(HERE):
        # test()
        commit()
        push()


@_contextmanager
def virtualenv():
    with cd(env.directory):
        with prefix(env.activate):
            yield


# Add tasks to deploy the code on the web server
def deploy():
    print("Deploying code")
    print("Code directory: %s" % env.directory)
    with settings(warn_only=True, sudo_user="root"):
        if run("test -d %s" % env.directory).failed:
            # Clone
            cmd = "git clone git@gitlab.computing.dcu.ie:dazcona/predictCS.git %s" % env.directory
            print("Running: %s" % cmd)
            sudo(cmd)
            # Virtual Environment
            sudo("rm -rf %s" % VIRTUAL_ENV)
            sudo("virtualenv %s" % VIRTUAL_ENV)
            with virtualenv():
                #run("pip freeze")
                sudo("pip install bcrypt Flask Flask-Bcrypt Flask-Bootstrap Flask-Login Flask-Mail Flask-Script "
                    "Flask-SQLAlchemy Flask-WTF Jinja2 numpy scikit-learn scipy sklearn SQLAlchemy Werkzeug WTForms") # coverage
                #run("pip freeze")
                run("deactivate")
    with cd(env.directory):
        # Pull
        sudo("git pull")
        # Touch the .wsgi file so that mod_wsgi triggers a reload of the application
        with shell_env(APP_SETTINGS="project.config.ProductionConfig"):
            sudo("touch %s" % WSGI_SCRIPT)
        #sudo("/etc/init.d/apache2 reload")


def testing():
    with virtualenv():
        run("whoami")
        sudo("whoami")
    with settings(sudo_user='root'):
        sudo("whoami") # prints 'root', password prompt bypassed
        run("cat ~/.ssh/id_rsa.pub")
        sudo("cat ~/.ssh/id_rsa.pub")
    with settings(sudo_user='david'):
        sudo("whoami") # prints 'david'
        run("cat ~/.ssh/id_rsa.pub")
        sudo("cat ~/.ssh/id_rsa.pub")
    with shell_env(APP_SETTINGS='config.DevelopmentConfig'):
        run("echo APP_SETTINGS is $APP_SETTINGS") # Only visible here