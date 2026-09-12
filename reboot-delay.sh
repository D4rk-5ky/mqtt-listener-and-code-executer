#!/bin/bash
(sleep 30 && reboot) &
echo $! > /tmp/reboot.pid