#!/bin/sh

[ "$VERBOSE" = true ] && echo "umounting /proc from target"
umount $TARGET/proc
