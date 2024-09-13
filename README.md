# meta-mediapipe-cmake

## Acknowledgements

bazel build borrowed outright from this repo https://git.yoctoproject.org/meta-tensorflow

tflite build derived from recipes of the same.

## Overview

This is a (work in progress) somewhat hacky attempt at trying to build mediapipe as a shared library with cmake.

We apply mediapipe patches to tflite and build that with bazel.

Then we parse mediapipes bazel configration to produce a tree of CMakeLists.txt and required source files.

Finally we build it.


# Some notes

* The tensorflow-lite recipe has version 2.18.0 - this is what it calls itself internally, however at the time of writing this is not a released version. Just some random stage in development that mediapipe wants to use. (https://github.com/google-ai-edge/mediapipe/blob/e252e5667e2be398dcc4c5d49ca134248e2111c8/WORKSPACE#L564)
* mediapipe dips heavily into the tensorflow internals, as such we package up a whole bunch of internal header files that it wants.
* testing / development is being done using face_detection_gpu example. At the time of writing it crashes parsing the graphs at startup related to looking for "options":
  * devtool modify mediapipe
  * devtool build mediapipe
  * cd workspace/sources/mediapipe
  * python3 ../../../../mediapipe/recipes-framework/mediapipe/files/bazel_to_cmake/mediapipe_bazel_to_cmake.py mediapipe/examples/desktop/face_detection face_detection_gpu
  * rsync out/* .
  * ./oe-workdir/temp/run.do_compile