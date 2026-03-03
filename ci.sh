#!/bin/sh

dropdb test_biblum

python -m pytest trials/tests -vv
