# meta-mediapipe-cmake

## Acknowledgements

bazel build borrowed outright from this repo https://git.yoctoproject.org/meta-tensorflow

tflite build derived from recipes of the same.

## Overview

This is a (work in progress) somewhat hacky attempt at trying to build mediapipe as a shared library with cmake.

We apply mediapipe patches to tflite and build that with bazel.

Then we parse mediapipes bazel configration to produce a tree of CMakeLists.txt and required source files.

Finally we build it.


