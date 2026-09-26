#!/bin/bash
(sleep 60 && reboot) &
echo $! > /tmp/reboot.pid
