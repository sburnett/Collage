#!/usr/bin/env python

import os.path
import os
import stat
import pwd
from optparse import OptionParser
import ConfigParser
import tempfile
import subprocess

run_script_text = '''cd %(directory)s;
export COLLAGE_USER=%(user)s;
export COLLAGE_HOME=%(directory)s;
export COLLAGE_ROOT=%(collage_root)s;
export PYTHONPATH=%(collage_root)s;
tmux new-session -s collage -d -n donation_server '%(django_admin)s runfcgi --settings=collage_donation.server.webapp_settings method=threaded socket=serv_misc/donation.socket pidfile=serv_misc/donation.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_donation '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/server/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n garbage 'python -m collage_donation.server.garbage_collection vectors; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n django 'sleep 10; %(django_admin)s runfcgi --settings=collage_donation.client.flickr_web_client.webapp_settings method=threaded socket=serv_misc/django.socket pidfile=serv_misc/django.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_flickr '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/client/flickr_web_client/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n flickr_upload_daemon 'python -m collage_donation.client.flickr_web_client.flickr_upload_daemon; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n get_latest_tags 'python -m collage_donation.client.flickr_web_client.get_latest_tags; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n centralized_donate 'sleep 15; python -m collage_donation.client.proxy_centralized_donate %(directory)s/centralized_photos; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n proxy_server 'python -m collage_apps.proxy.proxy_server vectors; echo Process terminated. Press ENTER to exit.; read';
tmux attach-session -t collage;'''

clean_script_text = '''cd %(directory)s;
rm -f waiting_keys.sqlite vectors/* uploads/* *.log estimate_db serv_misc/*.log;'''

clean_run_script_text = clean_script_text + run_script_text


def parse_options():
    usage = 'usage: %s [options] <run|clean|cleanrun>'
    parser = OptionParser(usage=usage)
    parser.set_defaults(config=None,
                        user=None,
                        directory=None,
                        root=None,
                        django=None)
    parser.add_option('-c', '--configuration', dest='config',
                      action='store', type='string',
                      help='Location of configuration file')
    parser.add_option('-u', '--user', dest='user',
                      action='store', type='string',
                      help='Switch to this user when running proxy')
    parser.add_option('-d', '--directory', dest='directory',
                      action='store', type='string',
                      help='Write proxy state to this directory')
    parser.add_option('-r', '--collage-root', dest='root',
                      action='store', type='string',
                      help='Use an alternative Collage root')
    parser.add_option('-a', '--django-admin', dest='django',
                      action='store', type='string',
                      help='django-admin executable to use')
    parser.add_option('-s', '--use-su', dest='su',
                      action='store_true',
                      help='Whether or not to use su (default is sudo).')
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error('Must specify command')

    user = options.user
    directory = options.directory
    collage_root = options.root
    django_admin = options.django
    use_su = options.su

    if options.config is not None:
        cfg = ConfigParser.ConfigParser()
        cfg.read(options.config)

        if cfg.has_section('proxy'):
            if user is None and cfg.has_option('proxy', 'user'):
                user = cfg.get('proxy', 'user')

            if directory is None \
                    and cfg.has_option('proxy', 'directory'):
                options.directory = cfg.get('proxy', 'directory')

            if collage_root is None and cfg.has_option('proxy', 'root'):
                collage_root = cfg.get('proxy', 'root')

            if django_admin is None \
                    and cfg.has_option('proxy', 'django_admin'):
                django_admin = cfg.get('proxy', 'django_admin')

            if use_su is None \
                    and cfg.has_option('proxy', 'use_su'):
                use_su = cfg.getboolean('proxy', 'use_su')
    
    if directory is None:
        if user is None:
            print 
            ans = raw_input('Running as current user; create a temporary directory to store state [Y/n]? ').strip()
            if len(ans) == 0 or ans[0] != 'n':
                directory = tempfile.mkdtemp()
            else:
                directory = '~'
        else:
            directory = '~%s' % user

    if user is None:
        user = pwd.getpwuid(os.getuid()).pw_name
        
    if collage_root is None:
        collage_root = os.path.dirname(__file__)

    if django_admin is None:
        django_admin = 'django-admin'

    if use_su is None:
        use_su = False

    directory = os.path.abspath(os.path.expanduser(directory))
    collage_root = os.path.abspath(collage_root)

    return (args[0], user, directory, collage_root, django_admin, use_su)

def main():
    (command, user, directory, collage_root, django_admin, use_su) = parse_options()

    if command == 'run':
        script_text = run_script_text
    elif command == 'clean':
        script_text = clean_script_text
    elif command == 'cleanrun':
        script_text = clean_run_script_text
    else:
        print 'Invalid command %s' % command
        return

    print 'Using the following settings:'
    print 'Doing command %s' % command
    print 'Running as user %s' % user
    print 'Writing proxy state to %s' % directory
    print 'Using Collage root %s' % collage_root

    (ofh, script_path) = tempfile.mkstemp(prefix='proxy')
    os.write(ofh, script_text % {'user': user,
                                 'directory': directory,
                                 'collage_root': collage_root,
                                 'django_admin': django_admin})
    os.close(ofh)
    os.chmod(script_path, stat.S_IRGRP|stat.S_IROTH|stat.S_IRUSR|stat.S_IWUSR)

    if use_su:
        cmd = 'su %s %s' % (user, script_path)
    else:
        cmd = 'sudo -u %s -i -- bash %s' % (user, script_path)
    print 'Running command %s' % cmd
    subprocess.call(cmd, shell=True)
    print 'Done with command'
    os.unlink(script_path)

if __name__ == '__main__':
    main()
