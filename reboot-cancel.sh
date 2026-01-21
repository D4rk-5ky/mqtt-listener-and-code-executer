#!/bin/bash
[ -f /tmp/reboot.pid ] && kill "$(cat /tmp/reboot.pid)" && rm /tmp/reboot.pid