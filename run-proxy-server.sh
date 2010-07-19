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
export COLLAGE_ROOT=$COLLAGE_ROOT
export COLLAGE_HOME=$COLLAGE_HOME
export COLLAGE_USER=$COLLAGE_USER
PYTHONPATH=$COLLAGE_ROOT;
screen -c $COLLAGE_ROOT/proxy-screenrc"
sudo -u $COLLAGE_USER -s -- script -q -c \"bash -c \\\"$cmd\\\"\" /dev/null
