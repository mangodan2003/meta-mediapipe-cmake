# meta-mediapipe-cmake

## Overview

This is a (work in progress) somewhat hacky attempt at trying to build mediapipe as a shared library with cmake.

We apply mediapipe patches to tflite and build that with cmake.

Then we parse mediapipes bazel configration to produce a tree of CMakeLists.txt and required source files.

Finally we build it.


