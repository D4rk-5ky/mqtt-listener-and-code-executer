#!/bin/bash
(sleep 30 && shutdown -P now) &
echo $! > /tmp/shutdown.pid
