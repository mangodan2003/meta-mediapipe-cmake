#!/bin/bash

src=$1
dst=$2

dirs=(
tensorflow/compiler/mlir/lite/utils
tensorflow/compiler/mlir/lite/experimental/remat
lite
tensorflow/lite/internal
tensorflow/lite/kernels/internal
tensorflow/lite/kernels/internal/optimized
tensorflow/lite/kernels/internal/reference
tensorflow/lite/kernels/internal/utils
tensorflow/lite/profiling
tensorflow/lite/profiling/telemetry
tensorflow/lite/profiling/telemetry/c
tensorflow/lite/c
tensorflow/lite/experimental
tensorflow/lite/experimental/remat
tensorflow/lite/experimental/resource
tensorflow/lite/core
tensorflow/lite/core/kernels
tensorflow/lite/core/c
tensorflow/lite/core/api
tensorflow/lite/core/async
tensorflow/lite/core/async/c
tensorflow/lite/core/async/interop
tensorflow/lite/core/async/interop/c
tensorflow/lite/schema
tensorflow/lite/delegates
tensorflow/lite/delegates/xnnpack
tensorflow/lite/delegates/gpu
tensorflow/lite/delegates/gpu/common
tensorflow/lite/delegates/gpu/common/google
tensorflow/lite/delegates/gpu/common/mediapipe
tensorflow/lite/delegates/gpu/gl/converters
)

files=(
tensorflow/compiler/mlir/lite/utils/string_utils.h
tensorflow/compiler/mlir/lite/utils/control_edges.h
tensorflow/compiler/mlir/lite/experimental/remat/metadata_util.h
tensorflow/lite/internal/signature_def.h
tensorflow/lite/logger.h
tensorflow/lite/builtin_op_data.h
tensorflow/lite/builtin_ops.h
tensorflow/lite/stateful_error_reporter.h
tensorflow/lite/interpreter.h
tensorflow/lite/portable_type_to_tflitetype.h
tensorflow/lite/graph_info.h
tensorflow/lite/model.h
tensorflow/lite/kernels/internal/common.h
tensorflow/lite/kernels/internal/compatibility.h
tensorflow/lite/kernels/internal/cppmath.h
tensorflow/lite/kernels/internal/optimized/neon_check.h
tensorflow/lite/kernels/padding.h
tensorflow/lite/kernels/internal/reference/dequantize.h
tensorflow/lite/kernels/internal/portable_tensor.h
tensorflow/lite/kernels/internal/runtime_shape.h
tensorflow/lite/kernels/internal/tensor_ctypes.h
tensorflow/lite/kernels/internal/tensor.h
tensorflow/lite/kernels/internal/types.h
tensorflow/lite/kernels/internal/utils/sparsity_format_converter.h
tensorflow/lite/kernels/kernel_util.h
tensorflow/lite/kernels/op_macros.h
tensorflow/lite/kernels/register.h
tensorflow/lite/memory_planner.h
tensorflow/lite/string_util.h
tensorflow/lite/util.h
tensorflow/lite/error_reporter.h
tensorflow/lite/profiling/root_profiler.h
tensorflow/lite/profiling/telemetry/telemetry_status.h
tensorflow/lite/profiling/telemetry/c/telemetry_setting.h
tensorflow/lite/profiling/telemetry/c/profiler.h
tensorflow/lite/profiling/telemetry/c/telemetry_setting_internal.h
tensorflow/lite/profiling/telemetry/profiler.h
tensorflow/lite/mutable_op_resolver.h
tensorflow/lite/minimal_logging.h
tensorflow/lite/allocation.h
tensorflow/lite/array.h
tensorflow/lite/c/builtin_op_data.h
tensorflow/lite/c/c_api.h
tensorflow/lite/c/c_api_types.h
tensorflow/lite/c/c_api_opaque.h
tensorflow/lite/c/common.h
tensorflow/lite/c/common_internal.h
tensorflow/lite/experimental/remat/metadata_util.h
tensorflow/lite/experimental/resource/initialization_status.h
tensorflow/lite/experimental/resource/resource_base.h
tensorflow/lite/type_to_tflitetype.h
tensorflow/lite/interpreter_options.h
tensorflow/lite/stderr_reporter.h
tensorflow/lite/model_builder.h
tensorflow/lite/core/c/builtin_op_data.h
tensorflow/lite/core/c/c_api.h
tensorflow/lite/core/c/c_api_opaque.h
tensorflow/lite/core/c/registration_external.h
tensorflow/lite/core/interpreter.h
tensorflow/lite/core/subgraph.h
tensorflow/lite/core/model.h
tensorflow/lite/core/kernels/register.h
tensorflow/lite/core/macros.h
tensorflow/lite/core/c/common.h
tensorflow/lite/core/c/c_api_types.h
tensorflow/lite/core/c/operator.h
tensorflow/lite/core/api/verifier.h
tensorflow/lite/core/api/error_reporter.h
tensorflow/lite/core/api/op_resolver.h
tensorflow/lite/core/api/profiler.h
tensorflow/lite/core/signature_runner.h
tensorflow/lite/core/model_builder.h
tensorflow/lite/core/async/async_subgraph.h
tensorflow/lite/core/async/async_kernel_internal.h
tensorflow/lite/core/async/async_signature_runner.h
tensorflow/lite/core/async/c/types.h
tensorflow/lite/core/async/interop/c/types.h
tensorflow/lite/core/interpreter_builder.h
tensorflow/lite/schema/schema_generated.h
tensorflow/lite/delegates/xnnpack/xnnpack_delegate.h
tensorflow/lite/delegates/gpu/common/model.h
tensorflow/lite/delegates/gpu/common/model_transformer.h
tensorflow/lite/delegates/gpu/common/status.h
tensorflow/lite/delegates/gpu/common/types.h
tensorflow/lite/delegates/gpu/common/util.h
tensorflow/lite/delegates/gpu/common/mediapipe/landmarks_to_transform_matrix.h
tensorflow/lite/delegates/gpu/common/mediapipe/transform_tensor_bilinear.h
tensorflow/lite/delegates/gpu/common/mediapipe/transform_landmarks.h
tensorflow/lite/delegates/gpu/common/model_builder.h
tensorflow/lite/delegates/gpu/common/model_builder_helper.h
tensorflow/lite/delegates/gpu/common/object_reader.h
tensorflow/lite/delegates/gpu/common/operations.h
tensorflow/lite/delegates/gpu/common/operation_parser.h
tensorflow/lite/delegates/gpu/common/gpu_info.h
tensorflow/lite/delegates/gpu/common/data_type.h
tensorflow/lite/delegates/gpu/common/tensor.h
tensorflow/lite/delegates/gpu/common/google/status_macros.h
tensorflow/lite/delegates/gpu/common/shape.h
tensorflow/lite/delegates/gpu/api.h
tensorflow/lite/delegates/gpu/gl/converters/util.h
tensorflow/lite/delegates/gpu/gl/gl_buffer.h
tensorflow/lite/delegates/gpu/gl/variable.h
tensorflow/lite/delegates/gpu/gl/command_queue.h
tensorflow/lite/delegates/gpu/gl/portable_gl31.h
tensorflow/lite/delegates/gpu/gl/gl_call.h
tensorflow/lite/delegates/gpu/gl/api2.h
tensorflow/lite/delegates/gpu/gl/gl_errors.h
tensorflow/lite/delegates/gpu/gl/gl_shader.h
tensorflow/lite/delegates/gpu/gl/gl_texture.h
tensorflow/lite/delegates/gpu/gl/gl_program.h
tensorflow/lite/delegates/gpu/gl/request_gpu_info.h
tensorflow/lite/delegates/gpu/gl_delegate.h
tensorflow/lite/interpreter_builder.h
tensorflow/lite/external_cpu_backend_context.h
tensorflow/lite/string_type.h
)

if [ "$src" = "$dst" ]
then
  printf "src and dst cannot be the same!\n"
  exit 1
fi


for d in ${dirs[@]}
do
 printf "Creating destination dir %s\n" "$dst/$d"
 mkdir -p "$dst/$d"
done

for f in ${files[@]}
do
 printf "Copying %s => %s\n" "$src/$f" "$dst/$f"
 cp "$src/$f" "$dst/$f"
done

