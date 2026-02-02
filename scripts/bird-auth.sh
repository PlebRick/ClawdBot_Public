#!/bin/bash
# Load bird credentials from protected env file
source ~/.clawdbot/bird-env
exec bird "$@"
