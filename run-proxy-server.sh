#!/bin/bash

# Change to this user before executing
COLLAGE_USER=collage

# This is the directory where mutable state will be written
COLLAGE_HOME=/home/collage

# This is the directory where the Collage source is located.
# It will be added to this session's PYTHONPATH
COLLAGE_ROOT=$HOME/git/collage

#####################################################################

# We will execute these commands when starting
# the screen session as the Collage user.
cmd="cd $COLLAGE_HOME;
export COLLAGE_USER=$COLLAGE_USER;
export COLLAGE_HOME=$COLLAGE_HOME;
export COLLAGE_ROOT=$COLLAGE_ROOT;
export PYTHONPATH=$COLLAGE_ROOT;
tmux new-session -s collage -d -n donation_server 'spawn-fcgi -s serv_misc/python-fastcgi.socket -n -- ${COLLAGE_ROOT}/collage_donation/server/server.py vectors 2>&1 | tee donation_server.log';
tmux new-window -t collage -n lighttpd_donation 'lighttpd -f ${COLLAGE_ROOT}/collage_donation/server/lighttpd.conf -D 2>&1 | tee lighttpd_donation.log';
tmux new-window -t collage -n garbage 'python -m collage_donation.server.garbage_collection vectors 2>&1 | tee garbage_collection.log';
tmux new-window -t collage -n django 'django-admin runfcgi --settings=collage_donation.client.flickr_web_client.settings method=threaded socket=serv_misc/django.sock pidfile=serv_misc/django.pid daemonize=false 2>&1 | tee django.log';
tmux new-window -t collage -n lighttpd-flickr 'lighttpd -f ${COLLAGE_ROOT}/collage_donation/client/flickr_web_client/lighttpd.conf -D 2>&1 | tee lighttpd_flickr.log';
tmux new-window -t collage -n flickr_upload_daemon 'python -m collage_donation.client.flickr_web_client.flickr_upload_daemon 2>&1 | tee flickr_upload_daemon.log';
tmux new-window -t collage -n get_latest_tags 'python -m collage_donation.client.flickr_web_client.get_latest_tags 2>&1 | tee get_latest_tags.log';
tmux new-window -t collage -n proxy_server 'python -m collage_apps.proxy.proxy_server vectors --local-dir=/tmp/dummy | tee proxy_server.log';
tmux attach-session -t collage;"
sudo -u $COLLAGE_USER -s -- bash -c \"$cmd\"
