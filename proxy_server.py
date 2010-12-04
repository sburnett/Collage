#!/usr/bin/env python2

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
export COMMUNITY_FLICKR_API_KEY=%(community_flickr_api_key)s;
export COMMUNITY_FLICKR_SECRET=%(community_flickr_secret)s;
export CENTRALIZED_FLICKR_API_KEY=%(centralized_flickr_api_key)s;
export CENTRALIZED_FLICKR_SECRET=%(centralized_flickr_secret)s;
export COLLAGE_LOGDIR=%(logdir)s;
tmux new-session -s collage -d -n donation_server '%(django_admin)s runfcgi --settings=collage_donation.server.webapp_settings method=threaded socket=serv_misc/donation.socket pidfile=serv_misc/donation.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_donation '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/server/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n garbage '%(python)s -m collage_donation.server.garbage_collection vectors; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n django 'sleep 10; %(django_admin)s runfcgi --settings=collage_donation.client.flickr_web_client.webapp_settings method=threaded socket=serv_misc/django.socket pidfile=serv_misc/django.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_flickr '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/client/flickr_web_client/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n flickr_upload_daemon '%(python)s -m collage_donation.client.flickr_web_client.flickr_upload_daemon; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n get_latest_tags '%(python)s -m collage_donation.client.flickr_web_client.get_latest_tags; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n centralized_donate 'sleep 15; %(python)s -m collage_donation.client.proxy_centralized_donate %(directory)s/centralized_photos; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n proxy_server '%(python)s -m collage_apps.proxy.proxy_server vectors; echo Process terminated. Press ENTER to exit.; read';
tmux attach-session -t collage;'''

clean_script_text = '''cd %(directory)s;
rm -f waiting_keys.sqlite vectors/* uploads/* *.log estimate_db serv_misc/*.log;'''

donation_script_text = '''cd %(directory)s;
export COLLAGE_USER=%(user)s;
export COLLAGE_HOME=%(directory)s;
export COLLAGE_ROOT=%(collage_root)s;
export PYTHONPATH=%(collage_root)s;
export COMMUNITY_FLICKR_API_KEY=%(community_flickr_api_key)s;
export COMMUNITY_FLICKR_SECRET=%(community_flickr_secret)s;
export CENTRALIZED_FLICKR_API_KEY=%(centralized_flickr_api_key)s;
export CENTRALIZED_FLICKR_SECRET=%(centralized_flickr_secret)s;
export COLLAGE_LOGDIR=%(logdir)s;
tmux new-session -s collage -d -n donation_server '%(django_admin)s runfcgi --settings=collage_donation.server.webapp_settings method=threaded socket=serv_misc/donation.socket pidfile=serv_misc/donation.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_donation '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/server/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n garbage '%(python)s -m collage_donation.server.garbage_collection vectors; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n django 'sleep 10; %(django_admin)s runfcgi --settings=collage_donation.client.flickr_web_client.webapp_settings method=threaded socket=serv_misc/django.socket pidfile=serv_misc/django.pid daemonize=false; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n lighttpd_flickr '/usr/sbin/lighttpd -f %(collage_root)s/collage_donation/client/flickr_web_client/lighttpd.conf -D; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n flickr_upload_daemon '%(python)s -m collage_donation.client.flickr_web_client.flickr_upload_daemon; echo Process terminated. Press ENTER to exit.; read';
tmux new-window -t collage -n get_latest_tags '%(python)s -m collage_donation.client.flickr_web_client.get_latest_tags; echo Process terminated. Press ENTER to exit.; read';
tmux attach-session -t collage;'''

clean_run_script_text = clean_script_text + run_script_text
clean_donation_script_text = clean_script_text + donation_script_text

commands = { 'run': run_script_text
           , 'clean': clean_script_text
           , 'cleanrun': clean_run_script_text
           , 'donation': donation_script_text
           , 'cleandonation': clean_donation_script_text
           }

def parse_options():
    usage = 'usage: %%s [options] <%s>' % ('|'.join(commands.keys()),)
    parser = OptionParser(usage=usage)
    parser.set_defaults(config=None)
    parser.add_option('-c', '--configuration', dest='config',
                      action='store', type='string',
                      help='Location of configuration file')
    options, rest = parser.parse_args()

    if len(rest) != 1:
        parser.error('Must specify command')

    command = rest[0]
    args = {}

    if options.config is not None:
        cfg = ConfigParser.ConfigParser()
        cfg.read(options.config)

        def parse_arg(section, name, arg=None, default=None, boolean=False):
            if arg is None:
                arg=name
            if cfg.has_section(section) and cfg.has_option(section, name):
                if boolean:
                    args[arg] = cfg.getboolean(section, name)
                else:
                    args[arg] = cfg.get(section, name)

        parse_arg('proxy', 'user')
        parse_arg('proxy', 'directory')
        parse_arg('proxy', 'root')
        parse_arg('proxy', 'django_admin')
        parse_arg('proxy', 'python')
        parse_arg('proxy', 'use_su', boolean=True)
        parse_arg('proxy', 'logdir')
        parse_arg('centralized', 'flickr_api_key', 'centralized_flickr_api_key')
        parse_arg('centralized', 'flickr_secret', 'centralized_flickr_secret')
        parse_arg('community', 'flickr_api_key', 'community_flickr_api_key')
        parse_arg('community', 'flickr_secret', 'community_flickr_secret')

    if 'directory' not in args:
        if 'user' not in args:
            ans = raw_input('Running as current user; create a temporary directory to store state [Y/n]? ').strip()
            if len(ans) == 0 or ans[0] != 'n':
                args['directory'] = tempfile.mkdtemp()
            else:
                args['directory'] = '~'
        else:
            args['directory'] = '~%s' % args['user']

    args.setdefault('user', pwd.getpwuid(os.getuid()).pw_name)
    args.setdefault('collage_root', os.path.dirname(__file__))
    args.setdefault('django_admin', 'django-admin')
    args.setdefault('python_exe', 'python')
    args.setdefault('use_su', False)
    args.setdefault('centralized_flickr_api_key', '')
    args.setdefault('centralized_flickr_secret', '')
    args.setdefault('community_flickr_api_key', '')
    args.setdefault('community_flickr_secret', '')
    args.setdefault('logdir', '')

    args['directory'] = os.path.abspath(os.path.expanduser(args['directory']))
    args['collage_root'] = os.path.abspath(args['collage_root'])

    return command, args

def main():
    command, args = parse_options()

    if command in commands:
        script_text = commands[command]
    else:
        print 'Invalid command %s' % command
        return

    print 'Using the following settings:'
    print 'Doing command %s' % command
    print 'Running as user %s' % args['user']
    print 'Writing proxy state to %s' % args['directory']
    print 'Using Collage root %s' % args['collage_root']

    (ofh, script_path) = tempfile.mkstemp(prefix='proxy')
    os.write(ofh, script_text % args)
    os.close(ofh)
    os.chmod(script_path, stat.S_IRGRP|stat.S_IROTH|stat.S_IRUSR|stat.S_IWUSR)

    if args['use_su']:
        cmd = 'su %s %s' % (args['user'], script_path)
    else:
        cmd = 'sudo -u %s -i -- bash %s' % (args['user'], script_path)
    print 'Running command %s' % cmd
    subprocess.call(cmd, shell=True)
    print 'Done with command'
    os.unlink(script_path)

if __name__ == '__main__':
    main()
