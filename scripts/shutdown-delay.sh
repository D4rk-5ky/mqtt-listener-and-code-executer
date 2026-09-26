#!/bin/bash
(sleep 60 && shutdown -P now) &
echo $! > /tmp/shutdown.pid
