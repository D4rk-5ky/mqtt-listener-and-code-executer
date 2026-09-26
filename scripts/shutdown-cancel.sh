#!/bin/bash
[ -f /tmp/shutdown.pid ] && kill "$(cat /tmp/shutdown.pid)" && rm /tmp/shutdown.pid