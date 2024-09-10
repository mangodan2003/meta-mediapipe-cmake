#!/usr/bin/python3

'''
This is a WIP attempt at building CMake files for building a mediapipe shared library.

See Jira https://earts.atlassian.net/browse/TR-6872
'''


from pywoodfortreesgui import *
import sys
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader 
from pathlib import Path
import traceback


print(f"arg: {sys.argv[1]}")

top_level_build_path=sys.argv[1]
rules=sys.argv[2:]

output_path = "out"
src_path = "src"
include_path = "include"

print(f"top_level_build_path: {top_level_build_path}")




res = {}

# tflite doen't have an installable build interface  - no cmake targets etc :(
# Is is intended to be bundled into the project that depends on it :(
# Here we make a list of link targets we can chuck in our cmake rules
# to make it work
tflite_libs = '''
Eigen3::Eigen
-ltensorflowlite
'''

# Translate bazel dep names into ones known to cmake
bazel_deps_map = {
    '@com_google_absl//absl/flags:flag':                'absl::flags',
    '@com_google_absl//absl/flags:parse':               'absl::flags_parse',
    '@com_google_absl//absl/log:absl_check':            'absl::absl_check',
    '@com_google_absl//absl/strings':                   'absl::strings',
    '@com_google_absl//absl/strings:str_format':        'absl::str_format',
    '@com_google_absl//absl/memory':                    'absl::memory',
    '@com_google_absl//absl/log:absl_log':              'absl::absl_log',
    '@com_google_absl//absl/status':                    'absl::status',
    '@com_google_absl//absl/types:optional':            'absl::optional',
    '@com_google_absl//absl/algorithm:container':       'absl::algorithm_container',
    '@com_google_absl//absl/strings:string_view':       'absl::string_view',
    '@com_google_absl//absl/types:span':                'absl::span',
    '@com_google_absl//absl/status:statusor':           'absl::statusor',
    '@com_google_absl//absl/time':                      'absl::time',
    '@com_google_absl//absl/synchronization':           'absl::synchronization',
    '@com_google_absl//absl/base:core_headers':         'absl::core_headers',
    '@com_google_absl//absl/functional:any_invocable':  'absl::any_invocable',
    '@com_google_absl//absl/functional:function_ref':   'absl::function_ref',
    '@com_google_absl//absl/container:flat_hash_map':   'absl::flat_hash_map',
    '@com_google_absl//absl/container:flat_hash_set':   'absl::flat_hash_set',
    '@com_google_absl//absl/meta:type_traits':          'absl::type_traits',
    '@com_google_absl//absl/base':                      'absl::base',
    '@com_google_absl//absl/container:btree':           'absl::btree',
    '@com_google_absl//absl/utility':                   'absl::utility',
    '@com_google_absl//absl/strings:has_ostream_operator':  'absl::has_ostream_operator',
    '@com_google_absl//absl/types:variant':             'absl::variant',
    '@com_google_absl//absl/container:node_hash_map':   'absl::node_hash_map',
    '@com_google_absl//absl/hash':                      'absl::hash',
    '@com_google_absl//absl/base:dynamic_annotations':  'absl::dynamic_annotations',
    '@com_google_absl//absl/debugging:leak_check':      'absl::leak_check',
    '@com_google_absl//absl/functional:bind_front':     'absl::bind_front',

    '@com_google_protobuf//:protobuf':                  'protobuf::libprotobuf',

    '@eigen_archive//:eigen3':                          'Eigen3::Eigen',

    '@com_github_glog_glog//:glog':                     'glog::glog',


    '@opencv':                                          '${OpenCV_LIBS}',


# This is a hacky list to avoid having to suck this lot in from the tflite soure tree :/
    '@org_tensorflow//tensorflow/lite:framework':       ('-ltensorflowlite','Eigen3::Eigen'),
    '@org_tensorflow//tensorflow/lite/core/api:op_resolver':            '',
    '@org_tensorflow//tensorflow/lite/core:framework':                  '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/common:data_type':  '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/common:shape':      '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/common:types':      ('-ltensorflowlite','Eigen3::Eigen'), #Was just the first thing in the list of deps for a buidl that failed cos it neede eigen
    '@org_tensorflow//tensorflow/lite/delegates/gpu:gl_delegate':       '-lgl_delegate',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl/converters:util': '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:gl_buffer':      '-lgl_buffer',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:gl_call':        '-lgl_delegate',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:command_queue':  '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:gl_program':     '-lgl_program',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:gl_shader':      '-lgl_shader',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:gl_texture':     '-lgl_delegate',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:request_gpu_info': '',
    '@org_tensorflow//tensorflow/lite/delegates/gpu/gl:variable':       '',
    '@org_tensorflow//tensorflow/lite/delegates/xnnpack:xnnpack_delegate': '',
    '@org_tensorflow//tensorflow/lite/kernels:builtin_ops':             '-ltensorflowlite',

}






def provided_args(**kwargs):
    """Returns the keyword arguments omitting None arguments."""
    return {k: v for k, v in kwargs.items() if v != None}

def get_arg_or_default(arg_name, default=None, **kwargs):
    return kwargs[arg_name] if arg_name in kwargs else default

def clean_dep(what):
    #if what.startswith("//"):
    #    what = what[2:]
    #print(f"clean_dep() Implement me! just returning {what} for now.")
    return what

def replace_suffix(string, old, new):
    """Returns a string with an old suffix replaced by a new suffix."""
    return string.endswith(old) and string[:-len(old)] + new or string

def replace_deps(deps, old, new, drop_google_protobuf = True):
    """Returns deps with an old suffix replaced by a new suffix.

    Args:
      deps: the specified dep targets.
      old: the suffix to remove.
      new: the suffix to insert.
      drop_google_protobuf: if true, omit google/protobuf deps.
    Returns:
      the modified dep targets.
    """
    if deps == None:
        return deps

    if drop_google_protobuf:
        deps = [dep for dep in deps if not dep.startswith("@com_google_protobuf//")]
    deps = [replace_suffix(dep, "any_proto", "cc_wkt_protos") for dep in deps]

    deps = [dep for dep in deps if not dep.endswith("_annotations")]
    deps = [replace_suffix(dep, old, new) for dep in deps]
    return deps


def write_templated_file(template, output_path, substitutions, log):
    try:
        template_content = template.read_text(encoding='UTF-8')
    except FileNotFoundError as e:
        log.info(f"Could not generate templated file, the source file {template} wasn't found")
        return
    for find, replace in substitutions.items():
        template_content = template_content.replace(find, replace)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True)

    with output_path.open("w") as f:
        f.write(template_content)



def fail(reason):
    raise RuntimeError(reason)

class Project:

    class Module:
        '''
        Each module contains a BUILD file which defines a number of buildable Rules
        Each instance of this represents a Module defined by the BUILD file
        '''
        class AbstractNamedModuleRule:
            '''
            Each BUILD file defines a number of buildable Rules (of various types cc_binary, cc_library etc)
            Each instance of this class represents an abstract rule
            '''
            def __init__(self, module, only_a_wrapper = False, **kwargs):
                self._required = False
                self._is_sub_rule = False
                self._module = module
                self._name = kwargs['name']
                self._full_path = f"{module.path}:{self._name}" if module is not None else self._name
                self.tools = get_arg_or_default('tools', [], **kwargs)

                self.visibility = get_arg_or_default('visibility', [], **kwargs)
                self._log_context = module._log_context.new(f"{self.__class__.__name__}[{self._name}]")
                self._log_context.info(f"{self.__class__.__name__} -> full_path : {self.full_path}, kwargs: {kwargs}")

                if not only_a_wrapper:
                    if self.full_path in module.rules:
                        if not self._is_sub_rule:
                            fail(f"Duplicate rule! Module module: {module.path} already has a rule called {self.full_path}")
                        else:
                            self._log_context.info("Not raising error for duplicate subrule.") 
                    else:
                        module.rules[self.full_path] = self

                self.always = get_arg_or_default('always', False, **kwargs)
                        
            @property
            def name(self):
                return self._name
            
            @property
            def full_path(self):
                return self._full_path
            
            @property
            def required(self):
                return self._required

            @required.setter
            def required(self, required):
                self._required = required


        class AbstractRule(AbstractNamedModuleRule):

            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                # When we parse the modules we get all the rules within that module
                # When we come to write CMakeLists.txt we only want to include rules we actually need
                # This flag will be set when resolving dependencies if we need this rule
                self.data = get_arg_or_default('data', [], **kwargs)
                self.deps = get_arg_or_default('deps', [], **kwargs)
                self.tools = get_arg_or_default('tools', [], **kwargs)

                self.sub_rules = []
                self._outs = get_arg_or_default('outs', [], **kwargs)
                for o in self._outs:
                    if o in module._src_provider_map:
                        fail("Duplicate src entry in outs!")
                    module._src_provider_map[o] = self

                self.srcs = get_arg_or_default('srcs', [], **kwargs)
                self._sub_rule_of = get_arg_or_default('sub_rule_of', None, **kwargs)
                self.testonly = get_arg_or_default('testonly', None, **kwargs)
                self.deps_as_rules = {}
                self._resolved = False

                # if self._sub_rule_of is not None:
                #     self._is_sub_rule = True
                #     self._sub_rule_of.add_sub_rule(self)
                #     self._sub_rule_of.module.rules[self.full_path] = self

            # QDH - can go once eigen/opencv QDH's sorted out
            @property
            def cmake_target_name(self):
                return ""

            @property
            def outs(self):
                return self._outs

            def resolve(self):
                if self._resolved: # Break any dependency loops
                    return
                
                # resolve src file dependencies for src files that are provided in the out list of another rule
                for s in self.srcs:
                    if s in self._module._src_provider_map:
                        dep = self._module._src_provider_map[s]
                        self._log_context.info(f"src file {s} of rule {self.full_path} is provided by {dep.full_path}")
                        self.deps.append(dep.full_path)
                        self.deps_as_rules[dep.full_path] = dep
                for d in self.deps_as_rules.values():
                    d.required = True
                self._resolved = True
                self.on_resolve()


            def on_resolve(self):
                '''
                Can be overriden by rules that need to do something once all their dependencies
                have been resolved (self.deps_as_rules has been populated)
                '''
                pass

            @property
            def resolved(self):
                return self._resolved

            @property
            def has_files(self):
                return True

            @property
            def name(self):
                return self._name


            @property
            def module(self):
                return self._module

            def add_sub_rule(self, rule):
                '''
                It's not immediatly obvious how Bazel handles directly nested rules, e.g.
                mediapipe_simple_subgraph goes on to call mediapipe_binary_graph, data_as_c_string etc.
                These must then be dependencies of the original mediapipe_simple_subgraph call however the class
                we generate for this doesn't have files we can make a cmake rule for. Therefore
                we add them to this list and look for them while resolving dependecies in such a way that we 
                bypass the (in this example) mediapipe_simple_subgraph rule.
                This means that if A depends on the result of a call to mediapipe_simple_subgraph, in the cmake output
                A will instead depend on all the things that mediapipe_simple_subgraph produced.
                '''
                self.sub_rules.append(rule.full_path)

            def copy_files(self, dest_dir, log, headers_only=False):
                if not self.has_files:
                    return

                log.info(f"Writing files for {self.full_path}")

                module_path = Path(self.module.path)

                dest_path = dest_dir / module_path

                dest_path.mkdir(parents=True, exist_ok=True)

                def copy_file(path):
                    if path.startswith('//'):
                        log.info(f"IMPLEMENT ME, can't handle path {path}")
                        return
                    src = module_path / path
                    dst = dest_path / path
                    log.info(f"    -> src file {dst}")
                    if not dst.exists():
                        if src.exists():
                            dst.hardlink_to(src)
                        else:
                            log.info(f"src file {src} does not exist!")

                if not headers_only:
                    for s in self.srcs:
                        copy_file(s)

                if hasattr(self, 'hdrs'):
                    for h in self.hdrs:
                        copy_file(h)

                if hasattr(self, 'textual_hdrs'):
                    for h in self.textual_hdrs:
                        copy_file(h)


        class Alias(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                self.actual = get_arg_or_default('actual', [], **kwargs)

            @property
            def required(self):
                return self._required

            @required.setter
            def required(self, required):
                self._required = False

            @property
            def cmake_target_name(self):
                if self.actual is None:
                    raise RuntimeError(f"actual has not been set for Alias {self.full_path}")
                return self.actual.cmake_target_name


        class AbstractCMakeListsGenerator(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
            
            @property
            def cmakelists_content(self):
                oops = f"cmakelists_content not implemented for f{self.__class__}" 
                raise RuntimeError(oops)

        class AbstractCCRule(AbstractCMakeListsGenerator):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                self.hdrs = get_arg_or_default('hdrs', [], **kwargs)
                self.textual_hdrs = get_arg_or_default('textual_hdrs', [], **kwargs)
                self.defines = get_arg_or_default('defines', [], **kwargs)
                module_path = module.path
                if module_path.startswith("//"):
                    module_path = module_path[2:]

                cmake_target_module_prefix = module_path.replace('/', '_')
                self._cmake_target_name = f"{cmake_target_module_prefix}_{self._name}"

            @property
            def cmake_target_name(self):
                return self._cmake_target_name


        class AbstractCMakeCompiledRule(AbstractCCRule):
            CMAKE_METHOD_EXECUTABLE = "add_executable"
            CMAKE_METHOD_LIBRARY = "add_library"

            CMAKE_LIBRARY_INTERFACE = "INTERFACE"
            CMAKE_LIBRARY_OBJECT = "OBJECT"
            CMAKE_LIBRARY_SHARED = "SHARED"

            def __init__(self, module, cmake_method, **kwargs):
                super().__init__(module, **kwargs)
                self.linkshared = get_arg_or_default("linkshared", 0, **kwargs)
                cmake_method = self.CMAKE_METHOD_LIBRARY if self.linkshared == 1 else cmake_method

                self.cmake_method = cmake_method
                self.linkopts = get_arg_or_default("linkopts", None, **kwargs)

                # If this is set this binary will be a dependency of a CMake target called tools
                # All members of this target are built by the mediapipe-native recipe as they must
                # be available to run as native tools for the main target build.
                # It can only be set for CCBinary via its set_is_tool()
                self._is_tool = False
                self.install = False

                self.library_type = self.CMAKE_LIBRARY_INTERFACE
                if len(self.srcs) > 0:
                    self.library_type = self.CMAKE_LIBRARY_OBJECT
                if self.linkshared:
                    self.library_type = self.CMAKE_LIBRARY_SHARED

            @property
            def is_tool(self):
                return self._is_tool
            
            @property
            def cmake_target_name(self):
                if self.install or self.is_tool:
                    return self._name
                return self._cmake_target_name

            @property
            def cmakelists_content(self):
                content = ""
                interface = ""
                library_type = ""

                if self.cmake_method == self.CMAKE_METHOD_LIBRARY:
                    if self.library_type == self.CMAKE_LIBRARY_INTERFACE:
                        interface = self.library_type
                    else:
                        library_type = self.library_type

                add_library_objects = self.library_type == self.CMAKE_LIBRARY_SHARED or self.cmake_method == self.CMAKE_METHOD_EXECUTABLE

                content += f"{self.cmake_method}({self.cmake_target_name} {interface} {library_type}\n"
                type_known = False
                for s in self.srcs:
                    content += f"{s}\n"
                    if s.endswith('.c') or s.endswith('.cc'):
                        type_known = True
                for h in self.hdrs:
                    # QDH
                    if h.startswith("//"):
                        self._log_context.info(f"Ignoring file {h}")
                        continue
                    content += f"{h}\n"

                if add_library_objects:
                    for d in self.deps_as_rules.values():
                        if not isinstance(d, Project.Module.AbstractCMakeCompiledRule):
                            continue
                        if not d.library_type == self.CMAKE_LIBRARY_OBJECT:
                            continue
                        content += f"$<TARGET_OBJECTS:{d.cmake_target_name}>\n"

                content += ")\n\n"
                if not type_known:
                    content += f"set_target_properties({self.cmake_target_name} PROPERTIES LINKER_LANGUAGE CXX)\n\n"


                # use to detect cyclic deps 
                added = []
                if len(self.deps) > 0:
                    content += f"target_link_libraries({self.cmake_target_name} {interface}\n"
                    for d in self.deps_as_rules.values():
                        
                        def add_target_link_library_deps(d):
                            if d in added:
                                return
                            added.append(d)
                            nonlocal content
                            # QDH for tflite that has no build interface :(
                            #if d.cmake_target_name.startswith('@org_tensorflow'):
                            #    if tflite_libs not in content:
                            #        content += tflite_libs
                            #    return

                            # lesser QDH
                            if d.cmake_target_name.startswith('@'):
                                if d.cmake_target_name in bazel_deps_map:
                                    mapped = bazel_deps_map[d.cmake_target_name]
                                    deps = []
                                    if isinstance(mapped, str):
                                        deps = [mapped]
                                    elif isinstance(mapped, tuple):
                                        deps = list(mapped)
                                    for dep in deps:
                                        dep = f"{dep}\n"
                                        if dep not in content:
                                            content += dep
                                    return
                                else:
                                    self._log_context.warning(f"No entry in map for {d.cmake_target_name}")

                            if not (isinstance(d, Project.Module.AbstractCMakeCompiledRule) or isinstance(d, Project.Module.CCProtoLibrary)):
                                return
                            if isinstance(d, Project.Module.CCBinary):
                                return
                            
                            #if isinstance(d, Project.Module.AbstractCMakeCompiledRule):
                            #if d.library_type == self.CMAKE_LIBRARY_INTERFACE:
                            dep = d.cmake_target_name
                            content += f"{dep}\n"

                            # For "top level" (the requested build target, or tools required to build it), list all (transitive) dependencies, not just direct ones
                            if self.install or self.is_tool:
                                for dd in d.deps_as_rules.values():
                                    add_target_link_library_deps(dd)

                        add_target_link_library_deps(d)


                       


                    if self.linkopts:
                        content += f"{self.linkopts[0]}\n"
                    content += ")\n\n"


                    content += f"set_property(TARGET {self.cmake_target_name} PROPERTY POSITION_INDEPENDENT_CODE ON)\n"

                    content += f"add_dependencies(artifacts {self.cmake_target_name})\n\n"
                        
                return content

        class CCBinary(AbstractCMakeCompiledRule):
            '''
            Each cc_binary entry in a BUILD file is represented by an instance of this class

            But with Bazel CCBinary doesn't necessarily mean an executable, it can be a shared library
            We default to cmakes add_executable but it might be changed by AbstractCMakeCompiledRule
            '''
            def __init__(self, module, **kwargs):

                super().__init__(module, "add_executable", **kwargs)

            def set_is_tool(self):
                self._is_tool = True


        class CCLibrary(AbstractCMakeCompiledRule):
            '''
            Each cc_library entry in a BUILD file is represented by an instance of this class

            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, "add_library", **kwargs)

        class CCLibraryWithTfLite(CCLibrary):
            '''
            Each cc_library_with_tflite entry in a BUILD file is represented by an instance of this class

            '''
            def __init__(self, module, **kwargs):
                deps = get_arg_or_default("deps", [], **kwargs)
                tflite_deps = get_arg_or_default("tflite_deps", [], **kwargs)
                deps.extend(tflite_deps)
                kwargs["deps"] = deps
                super().__init__(module, **kwargs)


        class CCProtoLibrary(AbstractCCRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)

            @property
            def cmakelists_content(self):
                rule_name = self.cmake_target_name
                include_name = self.srcs[0].replace(".proto", ".pb.h")
                content = "PROTOBUF_GENERATE_CPP(" + rule_name + "_sources " + rule_name + "_headers ${CMAKE_CURRENT_SOURCE_DIR}/" + self._module.path + "/" + self.srcs[0] + ")\n"
                content += "add_library(" + rule_name + " OBJECT  ${" + rule_name + "_sources} ${" + rule_name + "_headers})\n"
                content += f"set_property(TARGET {rule_name} PROPERTY POSITION_INDEPENDENT_CODE ON)\n"
                content += "target_include_directories(" + rule_name + " PUBLIC ${CMAKE_BINARY_DIR}/src)\n"
                content += 'set_source_files_properties(${' + rule_name + '_sources} PROPERTIES COMPILE_FLAGS " -Wno-maybe-uninitialized " )\n'
                content += "INSTALL(FILES ${CMAKE_CURRENT_BINARY_DIR}/" + f"{self._module.path}/{include_name} DESTINATION include/{self._module.path} OPTIONAL)\n\n"
                if len(self.deps_as_rules) > 0:
                    content += "target_link_libraries(" + rule_name + "\n"
                    for d in self.deps_as_rules.values():
                        if not isinstance (d, Project.Module.AbstractCMakeCompiledRule):
                            continue
                        content += f"{d.cmake_target_name}\n"
                    content += ")\n"
                content += "\n"
                return content


        class ConfigSetting(AbstractNamedModuleRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                self.define_values = kwargs['define_values'] if 'define_values' in kwargs else []

            @property
            def name(self):
                return self._name
            
        class CMakeCustomCommand(AbstractCCRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                self._cmd = get_arg_or_default('cmd', None, **kwargs)

            @property
            def cmakelists_content(self):
                cmd_string = self._cmd(self)
                #self._log_context.info(f"cmd_string: {cmd_string}")
                content =  "add_custom_command(\n"
                content += f"    OUTPUT {self.outs[0]}\n"
                content +=  "    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/src\n"
                content += f"    COMMAND {self._cmd(self)}\n"
                if len(self.srcs) > 0:
                    content += f"    DEPENDS {' '.join(self.srcs)}\n"                
                content += ")\n\n"

                #content +=  "add_custom_target(\n"
                #content += f"   {self.cmake_target_name} DEPENDS\n"
                #content +=  "    ${CMAKE_SOURCE_DIR}/" + f"{self.outs[0]}\n"
                #content +=  ")\n\n"
                return content        

        class DataAsCString:
            """Encodes the data from a file as a C string literal.

            This produces a text file containing the quoted C string literal. It can be
            included directly in a C++ source file.

            Args:
            name: The name of the rule.
            srcs: A list containing a single item, the file to encode.
            outs: A list containing a single item, the name of the output text file.
                    Defaults to the rule name.
            testonly: pass 1 if the graph is to be used only for tests.
            compatible_with: a list of environments the rule is compatible with.
            """
            def __init__(self, module, **kwargs):
                
                name = kwargs['name']
                testonly = get_arg_or_default('testonly', None, **kwargs)
                srcs = get_arg_or_default('srcs', [], **kwargs)
                outs = get_arg_or_default('outs', [], **kwargs)

                if len(srcs) != 1:
                    fail("srcs must be a single-element list")
                if outs == None:
                    outs = [name]
                encode_as_c_string = clean_dep("//mediapipe/framework/tool:encode_as_c_string")

                def cmd(rule):
                    '''
                    "$(location %s) \"$<\" > \"$@\"" % encode_as_c_string
                    '''
                    if len(rule.srcs) != 1:
                        raise RuntimeError("srcs must be a single-element list")
                    return f"encode_as_c_string {rule.module.path}/{rule.srcs[0]} > {rule.module.path}/{outs[0]} "
                module.genrule(
                    name = name,
                    srcs = srcs,
                    outs = outs,
                    cmd = cmd,
                    tools = [encode_as_c_string],
                    testonly = testonly,
                )

        class DirectDescriptorSet(AbstractRule):
            '''
            Concatenate all proto descriptors of immediate dependencies into a single file
            The Bazel build uses actions.run_shell for this instead of native.genrule used elsewhere.
            Both just run a shell command and I cannot find out why one would be used over the other.
            I think it has to do with how bazel rules are written, genrule just runs the shell, where as
            in this case the rule needs to do some internal logic and then run the shell command on the result.
            As we already have an implementation for genrule, just going to use that.
            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)

                def cmd(rule):
                    srcs = []

                    rule._log_context.info(f"cmd() for rule {rule.name}, deps: {rule.deps}, deps_as_rules: {rule.deps_as_rules}")

                    for dep in rule.deps_as_rules.values():
                        if isinstance(dep, Project.Module.ProtoLibrary):
                            srcs.append(dep.outs[0])

                    if len(srcs) < 1:
                        fail(f"No srcs resolved for {rule.name}")

                    # Set the rules sources as CMakeCustomCommand needs to write these as DEPENDS
                    rule.srcs = srcs
                    return f"cat {' '.join(srcs)} > {rule.module.path}/{rule.outs[0]}"

                module.genrule(
                    name = self.name,
                    srcs = [],
                    deps = self.deps,
                    outs =  [f"{self.name}-direct-descriptor-set.proto.bin"],
                    cmd = cmd,
                )




        class ExpandTemplate(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)

                self._log_context.info(f"ExpandTemplate(**kwargs: {kwargs}) Implement me!")
                template = kwargs['template']
                if template.startswith("//"):
                    path, filename = template[2:].split(':')
                    template = f"{path}/{filename}"
                elif template.startswith(':'):
                    template = f"{module.full_path}/{template[1:]}"


                output_filename = kwargs['out']
                template_output_path = Path(output_path) / src_path / module.path / output_filename
                substitutions = kwargs['substitutions']
                if ':' in template:
                    self._log_context.info(f"QDH, substituting : for / in {template}")
                    template = template.replace(':', '/')
                write_templated_file(Path(template), template_output_path, substitutions, self._log_context)

        class External():
            '''
            A dependency provided externally, e.g. a shared library installed by a package :)
            '''
            def __init__(self,  name):
                self._name = name
            
            @property
            def name(self):
                return self._name

            @property
            def full_path(self):
                return self._name

            @property
            def cmake_target_name(self):
                return self.name

            @property
            def has_files(self):
                return False

            @property
            def deps(self):
                return []
            
            @property
            def sub_rules(self):
                return []
            
            @property
            def tools(self):
                return []
            
            def resolve(self):
                pass

            @property
            def deps_as_rules(self):
                return {}
            
          
        class MediapipeCCProtoLibrary(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)
                cc_deps = kwargs['cc_deps']
                module.cc_proto_library(**provided_args(
                    name = self.name,
                    srcs = self.srcs,
                    visibility = self.visibility,
                    deps = cc_deps,
                    testonly = self.testonly,
                    cc_libs = ["@com_google_protobuf//:protobuf"],
                    protoc = "@com_google_protobuf//:protoc",
                    default_runtime = "@com_google_protobuf//:protobuf",
                    alwayslink = 1,
                ))

        class MediapipeOptionsLibrary(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)

                for k in ['name', 'deps', 'visibility', 'testonly']:
                    if k in kwargs:
                        del kwargs[k]

                proto_lib = kwargs['proto_lib']
                self.proto_lib = proto_lib
                proto_lib = proto_lib.name

                module.transitive_descriptor_set(
                    name = proto_lib + "_transitive",
                    deps = [f":{proto_lib}"],
                    testonly = self.testonly,
                )

                module.direct_descriptor_set(
                    name = proto_lib + "_direct",
                    deps = [f":{proto_lib}"],
                    testonly = self.testonly,
                )

                module.data_as_c_string(
                    name = self.name + "_inc",
                    srcs = [proto_lib + "_transitive-transitive-descriptor-set.proto.bin"],
                    outs = [proto_lib + "_descriptors.inc"],
                )

                def cmd(rule):
                    #cmd = ("$(location " + "//mediapipe/framework/tool:message_type_util" + ") " +
                    #    ("--input_path=$(location %s) " % (proto_lib + "_direct-direct-descriptor-set.proto.bin")) +
                    #    ("--root_type_macro_output_path=$(location %s) " % (self.name + "_type_name.h"))),
                    return f"message_type_util --input_path={module.path}/{proto_lib}_direct-direct-descriptor-set.proto.bin --root_type_macro_output_path={module.path}/{rule.name}.h"

                module.genrule(
                    name = self.name + "_type_name",
                    outs = [self.name + "_type_name.h"],
                    srcs = [proto_lib + "_direct-direct-descriptor-set.proto.bin"],
                    cmd = cmd,
                    tools = ["//mediapipe/framework/tool:message_type_util"],
                    visibility = self.visibility,
                    testonly = self.testonly,
                )
                module.expand_template(
                    name = self.name + "_cc",
                    template = clean_dep("//mediapipe/framework/tool:options_lib_template.cc"),
                    out = self.name + ".cc",
                    substitutions = {
                        "{{MESSAGE_NAME_HEADER}}": module.package_name() + "/" + self.name + "_type_name.h",
                        "{{MESSAGE_PROTO_HEADER}}": module.package_name() + "/" + proto_lib.replace("_proto", ".pb.h"),
                        "{{DESCRIPTOR_INC_FILE_PATH}}": module.package_name() + "/" + proto_lib + "_descriptors.inc",
                    },
                    testonly = self.testonly,
                )
                module.cc_library(
                    name = proto_lib.replace("_proto", "_options_registry"),
                    srcs = [
                        self.name + ".cc",
                        proto_lib + "_descriptors.inc",
                        self.name + "_type_name.h",
                    ],
                    deps = [
                        clean_dep("//mediapipe/framework:calculator_framework"),
                        clean_dep("//mediapipe/framework/port:advanced_proto"),
                        clean_dep("//mediapipe/framework/tool:options_registry"),
                        proto_lib.replace("_proto", "_cc_proto"),
                    ] + self.deps,
                    alwayslink = 1,
                    visibility = self.visibility,
                    testonly = self.testonly,
                    features = ["-no_undefined"],
                    **kwargs
                )
                module.mediapipe_reexport_library(
                    name = self.name,
                    actual = [
                        proto_lib.replace("_proto", "_cc_proto"),
                        proto_lib.replace("_proto", "_options_registry"),
                    ],
                    visibility = self.visibility,
                    testonly = self.testonly,
                    **kwargs
                )


        class MediapipeBinaryGraph:
            '''
            Each mediapipe_binary_graph entry in a BUILD file is represented by an instance of this class

            '''
            def __init__(self, module, **kwargs):
               
                graph = get_arg_or_default('graph', None, **kwargs)
                output_name = get_arg_or_default('output_name', None, **kwargs)
                name = kwargs['name']
                testonly = get_arg_or_default('testonly', None, **kwargs)
                deps = get_arg_or_default('deps', [], **kwargs)

                if graph is None:
                    fail("No input graph file specified.")

                if  output_name is None:
                    fail("Must specify the output_name.")

                transitive_protos = Project.Module.TransitiveProtos(
                    module,
                    name = name + "_gather_cc_protos",
                    deps = deps,
                    testonly = testonly,
                )


                # Mediapipes Bazel build compiles a native binary which it then runs to convert the graph (.pbtxt) to binary (.binaryp)
                # But it seems we can just do this with protoc :/
                # module.cc_binary(
                #     always = True, # Force this to always build for now.
                #     name = name + "_text_to_binary_graph",
                #     visibility = ["//visibility:private"],
                #     deps = [
                #         clean_dep("//mediapipe/framework/tool:text_to_binary_graph"),
                #         name + "_gather_cc_protos",
                #     ],
                #     tags = ["manual"],
                #     testonly = testonly,
                # )

                # module.genrule(
                #     name = name,
                #     srcs = [graph],
                #     outs = [output_name],
                #     cmd = (
                #         "$(location " + name + "_text_to_binary_graph" + ") " +
                #         ("--proto_source=$(location %s) " % graph) +
                #         ("--proto_output=\"$@\" ")
                #     ),
                #     tools = [name + "_text_to_binary_graph"],
                #     testonly = testonly,
                # )
                def cmd(rule):
                    for dep_path, dep in rule.deps_as_rules.items():
                        # dep should be an instance of TransitiveProtos
                        rule._log_context.info(f"cmd() adding cmd for  {dep_path}")
                        protos = dep.protos
                        return f"cat {rule.module.path}/{graph} | protoc --encode mediapipe.CalculatorGraphConfig {' '.join(protos)} > {rule.module.path}/{output_name}"

                module.genrule(
                    name = name,
                    deps = ["//"+transitive_protos.full_path],
                    srcs = [graph],
                    outs = [output_name],
                    cmd = cmd,
                    tools = ["protoc"]
                )
               

        class MediapipeProtoLibrary(AbstractRule):
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)

                def_proto = get_arg_or_default('def_proto', True, **kwargs)
                def_cc_proto = get_arg_or_default('def_cc_proto', True, **kwargs)
                def_options_lib = get_arg_or_default('def_options_lib', True, **kwargs)
                proto_deps = get_arg_or_default('proto_deps', [], **kwargs)

                if def_proto:
                    module.proto_library(**provided_args(
                        name = self.name,
                        srcs = self.srcs,
                        deps = self.deps,
                        visibility = self.visibility,
                        testonly = self.testonly,
                    ))

                if def_cc_proto:
                    cc_deps = replace_deps(self.deps, "_proto", "_cc_proto", False)
                    module.mediapipe_cc_proto_library(**provided_args(
                        name = replace_suffix(self.name, "_proto", "_cc_proto"),
                        srcs = self.srcs,
                        deps = proto_deps,
                        cc_deps = cc_deps,
                        visibility = self.visibility,
                        testonly = self.testonly,
                    ))

                if def_options_lib:
                    cc_deps = replace_deps(self.deps, "_proto", "_cc_proto")
                    module.mediapipe_options_library(**provided_args(
                        name = replace_suffix(self.name, "_proto", "_options_lib"),
                        proto_lib = self,
                        deps = cc_deps,
                        visibility = self.visibility,
                        testonly = self.testonly,
                    ))


        class MediapipeSimpleSubGraph:
            '''
            Each mediapipe_simple_subgraph entry in a BUILD file is represented by an instance of this class

            '''
            def __init__(self, module, **kwargs):
               
                graph = get_arg_or_default('graph', None, **kwargs)
                register_as = get_arg_or_default('register_as', None, **kwargs)
                name = kwargs['name']
                testonly = get_arg_or_default('testonly', None, **kwargs)
                deps = get_arg_or_default('deps', [], **kwargs)
                visibility = get_arg_or_default('visibility', None, **kwargs)

                graph_base_name = name
                module.mediapipe_binary_graph(
                    name = name + "_graph",
                    graph = graph,
                    output_name = graph_base_name + ".binarypb",
                    deps = deps,
                    testonly = testonly,
                )

                module.data_as_c_string(
                    name = name + "_inc",
                    srcs = [graph_base_name + ".binarypb"],
                    outs = [graph_base_name + ".inc"],
                )

                # cc_library for a linked mediapipe graph.
                module.expand_template(
                    name = name + "_linked_cc",
                    template = clean_dep("//mediapipe/framework/tool:simple_subgraph_template.cc"),
                    out = name + "_linked.cc",
                    substitutions = {
                        "{{SUBGRAPH_CLASS_NAME}}": register_as,
                        "{{SUBGRAPH_INC_FILE_PATH}}": module.package_name() + "/" + graph_base_name + ".inc",
                    },
                    testonly = testonly,
                )

                tflite_deps = get_arg_or_default('tflite_deps]', None, **kwargs)

                for k in ['name', 'deps', 'visibility']:
                    if k in kwargs:
                        del kwargs[k]

                if not tflite_deps:
                    module.cc_library(
                        name = name,
                        srcs = [
                            name + "_linked.cc",
                            graph_base_name + ".inc",
                        ],
                        deps = [
                            clean_dep("//mediapipe/framework:calculator_framework"),
                            clean_dep("//mediapipe/framework:subgraph"),
                        ] + deps + [f"//{module.path}:{name}_graph"],
                        alwayslink = 1,
                        visibility = visibility,
                        testonly = testonly,
                        **kwargs
                    )
                else:
                    module.cc_library_with_tflite(
                        name = name,
                        srcs = [
                            name + "_linked.cc",
                            graph_base_name + ".inc",
                        ],
                        tflite_deps = tflite_deps,
                        deps = [
                            clean_dep("//mediapipe/framework:calculator_framework"),
                            clean_dep("//mediapipe/framework:subgraph"),
                        ] + deps,
                        alwayslink = 1,
                        visibility = visibility,
                        testonly = testonly,
                        **kwargs
                    )

        class ProtoLibrary(CMakeCustomCommand):
            '''
            Generate a binary descriptor set for the provided .protoc
            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)

                if len(self.srcs) != 1:
                    fail("srcs must be a single-element list")

                self._outs = [f"{module.path}/{self.srcs[0]}.bin"]
                self.tools = ["protoc"]

                def cmd(rule):
                    rule._log_context.info(f"Generate descriptor set for {rule.name}")
                    return f"protoc -o {rule.outs[0]} {rule.module.path}/{rule.srcs[0]}"

                self._cmd = cmd



        class ReExportLibrary(AbstractRule):
            '''
            Search all deps for .proto files and make a list of them
            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)
                actual = get_arg_or_default('actual', [], **kwargs)

                for k in ['name', 'deps']:
                    if k in kwargs:
                        del kwargs[k]

                module.cc_library(
                    name = self.name,
                    deps = [':' + a for a in actual],
                    textual_headers = actual,
                    **kwargs
                )


        class TransitiveDescriptorSet(AbstractRule):
            '''
            Concatenate all proto descriptors of all dependencies into a single file
            The Bazel build uses actions.run_shell for this instead of native.genrule used elsewhere.
            Both just run a shell command and I cannot find out why one would be used over the other.
            I think it has to do with how bazel rules are written, genrule just runs the shell, where as
            in this case the rule needs to do some internal logic and then run the shell command on the result.
            As we already have an implementation for genrule, just going to use that.
            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, only_a_wrapper=True, **kwargs)
                self.descriptors = set()
                def cmd(rule):
                    srcs = []

                    rule._log_context.info(f"cmd() for rule {rule.name}, deps: {rule.deps}, deps_as_rules: {rule.deps_as_rules}")

                    for dep in rule.deps_as_rules.values():
                        if isinstance(dep, Project.Module.ProtoLibrary):
                            srcs.append(dep.outs[0])

                    if len(srcs) < 1:
                        fail(f"No srcs resolved for {rule.name}")

                    # Set the rules sources as CMakeCustomCommand needs to write these as DEPENDS
                    rule.srcs = srcs

                    return f"cat {' '.join(srcs)} > {rule.module.path}/{rule.outs[0]}"

                module.genrule(
                    name = self.name,
                    srcs = [],
                    deps = self.deps,
                    outs = [f"{self.name}-transitive-descriptor-set.proto.bin"],
                    cmd = cmd,
                )

            def on_resolve(self):
                '''
                Now all our deps are resolved, find all the descriptor files...
                '''
                self._log_context.info(f"Resolving transitive descriptors for {self.full_path}")
                resolved = []
                def find_descriptors(rule):
                    if rule in resolved: # Break any dependency loops
                        return
                    resolved.append(rule)

                    if isinstance(rule, Project.Module.ProtoLibrary):
                        self.descriptors.append(f"{rule.module.path}/{rule.out[0]}")
                        self._log_context.info(f"    {rule.full_path} has {rule.out[0]}")

                    for d in rule.deps_as_rules.values():
                        find_descriptors(d)

                find_descriptors(self)

                self._log_context.info(f"descriptors: {self.descriptors}")


        class TransitiveProtos(AbstractRule):
            '''
            Search all deps for .proto files and make a list of them
            '''
            def __init__(self, module, **kwargs):
                super().__init__(module, **kwargs)
                self.protos = []

            def on_resolve(self):
                '''
                Now all our deps are resolved, find all the .proto files...
                '''
                self._log_context.info(f"Resolving protos for {self.full_path}")
                resolved = []
                def find_protos(rule):
                    if rule in resolved: # Break any dependency loops
                        return
                    resolved.append(rule)

                    if isinstance(rule, Project.Module.CCProtoLibrary):
                        self.protos.append(f"{rule.module.path}/{rule.srcs[0]}")
                        self._log_context.info(f"    {rule.full_path} has {rule.srcs[0]}")

                    for d in rule.deps_as_rules.values():
                        find_protos(d)

                find_protos(self)

                self._log_context.info(f"protos: {self.protos}")



        def __init__(self, parent_log_context, path):
            self._path = path
            self._selects = None
            self._more_selects = None
            self.defines = {}
            self.config_settings = {}
            self._log_context = parent_log_context.new(f"Module[{path}]")
            self._log_context.info("Parsing module...")
            self.rules = {}
            spec = spec_from_loader("Module", SourceFileLoader("Module", f"{path}/BUILD"))
            module = module_from_spec(spec)

            # rules can specify entries in their srcs list that come from other rules, where those rules
            # have declared the file in there outs list.
            # this is used as a lookup from the srcs list of one rule to the rule that declares the file in its ours list.
            self._src_provider_map = {}


            module.alias = self.alias
            module.android_library = self.android_library
            module.bzl_library = self.bzl_library
            module.cc_binary = self.cc_binary
            module.cc_library = self.cc_library
            module.cc_library_with_tflite = self.cc_library_with_tflite
            module.cc_test = self.cc_test
            module.cc_test_with_tflite = self.cc_test_with_tflite
            module.cmake = self.cmake
            module.config_setting = self.config_setting
            module.data_as_c_string = self.data_as_c_string
            module.exports_files = self.exports_files
            module.filegroup = self.filegroup
            module.genrule = self.genrule
            module.glob = self.glob
            module.ios_unit_test = self.ios_unit_test
            module.java_plugin = self.java_plugin
            module.java_library = self.java_library
            module.java_import = self.java_import
            module.licenses = self.licenses
            module.load = self.load
            module.mediapipe_binary_graph = self.mediapipe_binary_graph
            module.mediapipe_cc_test = self.mediapipe_cc_test
            module.mediapipe_files = self.mediapipe_files
            module.mediapipe_proto_library = self.mediapipe_proto_library
            module.mediapipe_register_type = self.mediapipe_register_type
            module.mediapipe_simple_subgraph = self.mediapipe_simple_subgraph
            module.metal_library = self.metal_library
            module.more_selects = self.more_selects
            module.objc_library = self.objc_library
            module.package = self.package
            module.package_group = self.package_group
            module.select = self.select
            module.selects = self.selects
            module.test_suite = self.test_suite

            spec.loader.exec_module(module)

            self.resolve_src_out_file_dependencies()


        def resolve_src_out_file_dependencies(self):
            '''
            If a file listed in srcs of a rule within a module exists within
            outs of a rule with the same module, then the 2nd rule is automatically a dependency
            of the first
            '''
            # First, create a map of out files to the rule that provides them
            out_rule_map = {}
            for rule in self.rules.values():
                rule_name = rule.name
                if not isinstance(rule, Project.Module.AbstractRule):
                    continue
                self._log_context.info(f"resolve_src_out_file_dependencies() resolving {rule.name}, outs: {rule.outs}")
                for out in rule.outs:
                    if out in out_rule_map:
                        conflicting_rule = out_rule_map[out].name
                        fail(f"Duplicate out file! {out}:  provided by {rule_name} conflicts with that of {conflicting_rule}!")
                    else:
                        out_rule_map[out] = rule_name

            # Now walk srcs of each rule to find any that exist in out_rule_map
            for rule in self.rules.values():
                rule_name = rule.name
                if not isinstance(rule, Project.Module.AbstractRule):
                    continue
                for src in rule.srcs:
                    if src in out_rule_map:
                        dependency = ':' + out_rule_map[src]
                        rule.deps.append(dependency)
                        self._log_context.info(f"resolve_src_out_file_dependencies() {rule_name} depends on {dependency} (for src file {src})")


        @property
        def path(self):
            return self._path

        @property
        def deps(self):
            return self._deps

        def package_name(self):
            '''
            required for code snippets pinched directly from mediapipes .bzl files
            Seems to just be the same thing as self._path
            '''
            return self._path

        # Bazel Build files API

        def alias(self, **kwargs):
            Project.Module.Alias(self, **kwargs)

        def android_library(self, **kwargs):
            self._log_context.info(f"android_library(**kwargs: {kwargs}) Implement me!")

        def bzl_library(self, **kwargs):
            self._log_context.info(f"bzl_library(**kwargs: {kwargs}) Implement me!")

        def data_as_c_string(self, **kwargs):
            Project.Module.DataAsCString(self, **kwargs)

        def expand_template(self, **kwargs):
            Project.Module.ExpandTemplate(self, **kwargs)

        def licenses(self, licenses):
            self._log_context.info(f"licenses() licenses: {licenses}")


        def package(self, default_visibility = [], **kwargs):
            self._log_context.info(f"package() default_visibility: {default_visibility}")

        def exports_files(self, files = [], srcs = [], visibility = []):
            self._log_context.info(f"exports_file(files: {files}, srcs: {srcs}, visibility: {visibility}) Implement me!")

        def cc_binary(self, **kwargs):
            Project.Module.CCBinary(self, **kwargs)

        def cc_library(self, **kwargs):
            Project.Module.CCLibrary(self, **kwargs)


        def cc_library_with_tflite(self, **kwargs):
            Project.Module.CCLibraryWithTfLite(self, **kwargs)

        def cc_proto_library(self, **kwargs):
            Project.Module.CCProtoLibrary(self, **kwargs)

        def cc_test(self, **kwargs):
            #self._log_context.info(f"cc_test(**kwargs: {kwargs}) Implement me!")
            pass

        def cc_test_with_tflite(self, **kwargs):
            self._log_context.info(f"cc_test_with_tflite(**kwargs: {kwargs}) Implement me!")

        def cmake(self, **kwargs):
            self._log_context.info(f"cmake(**kwargs: {kwargs}) Implement me!")

        def config_setting(self, **kwargs):
            self._log_context.info(f"config_setting(**kwargs: {kwargs})")
            cs = Project.Module.ConfigSetting(self, **kwargs)
            self.config_settings[cs.full_path] = cs

        def direct_descriptor_set(self, **kwargs):
            Project.Module.DirectDescriptorSet(self, **kwargs)

        def filegroup(self, **kwargs):
            self._log_context.info(f"mediapipe_cc_test(**kwargs: {kwargs}) Implement me!")

        def genrule(self, **kwargs):
            Project.Module.CMakeCustomCommand(self, **kwargs)

        def glob(self, include, exclude=[], exclude_directories=1, allow_empty=True):
            self._log_context.info(f"glob() Implement me!")


        def java_plugin(self, **kwargs):
            self._log_context.info(f"java_plugin(**kwargs: {kwargs}) Implement me!")

        def java_library(self, **kwargs):
            self._log_context.info(f"java_library(**kwargs: {kwargs}) Implement me!")
        
        def java_import(self, **kwargs):
            self._log_context.info(f"java_import(**kwargs: {kwargs}) Implement me!")

        
        def ios_unit_test(self, **kwargs):
            self._log_context.info(f"ios_unit_test(**kwargs: {kwargs}) Implement me!")

        def load(self, module, rule, another_rule=None):
            self._log_context.info(f"load(module: {module}, rule: {rule}, another_rule: {another_rule}) Implement me!")

        def metal_library(self, **kwargs):
            self._log_context.info(f"metal_library(**kwargs: {kwargs}) Implement me!")

        def mediapipe_binary_graph(self, **kwargs):
             Project.Module.MediapipeBinaryGraph(self, **kwargs)

        def mediapipe_files(self, **kwargs):
            self._log_context.info(f"mediapipe_files(**kwargs: {kwargs}) Implement me!")

        def mediapipe_cc_proto_library(self, **kwargs):
            Project.Module.MediapipeCCProtoLibrary(self, **kwargs)

        def mediapipe_options_library(self, **kwargs):
            Project.Module.MediapipeOptionsLibrary(self, **kwargs)

        def mediapipe_proto_library(self, **kwargs):
            Project.Module.MediapipeProtoLibrary(self, **kwargs)
     
        def mediapipe_reexport_library(self, **kwargs):
            Project.Module.ReExportLibrary(self, **kwargs)

        def mediapipe_register_type(self, **kwargs):
            self._log_context.info(f"mediapipe_register_type(**kwargs: {kwargs}) Implement me!")

        def mediapipe_simple_subgraph(self, **kwargs):
            Project.Module.MediapipeSimpleSubGraph(self, **kwargs)

        def mediapipe_cc_test(self, **kwargs):
            self._log_context.info(f"mediapipe_cc_test(**kwargs: {kwargs}) Implement me!")

        def objc_library(self, **kwargs):
            self._log_context.info(f"objc_library(**kwargs: {kwargs}) Implement me!")

        def package_group(self, **kwargs):
            self._log_context.info(f"package_group(**kwargs: {kwargs}) Implement me!")

        def proto_library(self, **kwargs):
            Project.Module.ProtoLibrary(self, **kwargs)

        def select(self, what):
            if "//conditions:default" in what:
                return what[ "//conditions:default"]

            self._log_context.info(f"select(what: {what}) Implement me! returning []")
            return []

        def test_suite(self, **kwargs):
            self._log_context.info(f"test_suite(**kwargs: {kwargs}) Implement me!")

        def transitive_protos(self, **kwargs):
            Project.Module.TransitiveProtos(self, **kwargs)

        def transitive_descriptor_set(self, **kwargs):
            Project.Module.TransitiveDescriptorSet(self, **kwargs)


        @property
        def selects(self):
            if self._selects is None:

                class Selects:
                    def __init__(self, parent_log_context):
                        self._log_context = parent_log_context.new(f"Selects")

                    def config_setting_group(self, **kwargs):
                        self._log_context.info(f"config_setting_group(kwargs: {kwargs}) Implement me!")

                    def with_or(self, obj):
                        if "//conditions:default" in obj:
                            return obj[ "//conditions:default"]

                        self._log_context.info(f"selects.with_or(what: {obj}) Implement me! returning []")
                        return []



                self._selects = Selects(self._log_context)
            return self._selects

        @property
        def more_selects(self):
            if self._more_selects is None:

                class MoreSelects:
                    def __init__(self, parent_log_context):
                        self._log_context = parent_log_context.new(f"MoreSelects")

                    def config_setting_negation(self, **kwargs):
                        self._log_context.info(f"config_setting_negation(kwargs: {kwargs}) Implement me!")

 
                self._more_selects = MoreSelects(self._log_context)
            return self._more_selects




    def __init__(self, top_level_build_path, rules):
        self._licenses = []
        self.modules = {}

        self._log_context = get_log_manager().new("Project")

        deps_log = get_log_manager().new("Dependecies chain")
        srcs_log = deps_log.new("srcs")

        #top_level_build_module = Project.Module(self._log_context, top_level_build_path)
        top_level_build_module = self.get_or_load_module(f"//{top_level_build_path}")


        deps_resolved = {}
        deps_not_resolved = set()

        # First walk all the modules that contain required dependencies of the requested rules
        for a in rules:
            full_path = f"{top_level_build_path}:{a}"
            deps_log.info(f"Resolving dependencies for rule {full_path}....")
            try:
                a = top_level_build_module.rules[full_path]
                a.install = True
            except KeyError as e:
                deps_log.info(f"!!! Missing dependency !!! : {full_path}, we have: {top_level_build_module.rules.keys()}")
                fail("Missing Dependency")

            a.required = True

            def resolve_deps(rule, depth):
                if rule.full_path in deps_resolved:
                    deps_log.info(f"resolve_deps() {' '*depth} {rule.full_path} already resolved.")
                    return
                rule.required = True

                if isinstance(rule, Project.Module.MediapipeOptionsLibrary):
                    deps_log.info(f"resolve_deps() {' '*depth} {rule.full_path} is an instance of Project.Module.MediapipeOptionsLibrary!")
                    resolve_deps(rule.proto_lib, depth+1)

                if isinstance(rule, Project.Module.CMakeCustomCommand):
                    deps_log.info(f"resolve_deps() {' '*depth} {rule.full_path} is an instance of Project.Module.CMakeCustomCommand!")



                # We need these binaries as native to build dependencies
                # They will get built by a -native recipe and then used
                # by the target recipe
                if isinstance(rule, Project.Module.CCLibrary):
                    graph_binary = rule.full_path + "_graph_text_to_binary_graph"
                    if graph_binary in rule.module.rules:
                        deps_log.info(f"Including graph binary : {graph_binary}")
                        if not graph_binary.startswith(":"):
                            graph_binary = "//" + graph_binary
                        rule.deps.append(graph_binary)

                deps_log.info(f"resolve_deps() {'    '*depth} {rule.full_path} depends on:")
                deps_log.info(f"deps: {rule.deps}")
                deps_log.info(f"tools: {rule.tools}")
                deps_log.info(f"sub_rules: {rule.sub_rules}")


                def resolve_dep(d, is_tool=False):
                    tool_str = "(is a tool)" if is_tool else ""
                    deps_log.info(f"resolve_deps() {'    '*depth} {d} {tool_str} resolving...")
                    try:
                        dependency_rule = self.rule_from_dep_string(rule.module, d)
                        if dependency_rule:
                            if is_tool:
                                dependency_rule.set_is_tool()
                            rule.deps_as_rules[d] = dependency_rule
                            deps_log.info(f"resolve_deps() {'    '*depth}  {dependency_rule.full_path}")
                            resolve_deps(dependency_rule, depth+1)
                        else:
                            deps_log.info(f"resolve_deps() {'    '*depth}  self.rule_from_dep_string() yield'd None for rule.module: {rule.module.path}, d: {d}")

                           
                    except Exception as e:
                        deps_log.info(f"resolve_deps() {'    '*depth} module {rule.module.path}, rule {rule.name} depends on {d} but it could not be resolved (exception: {e})")
                        deps_log.info(f"resolve_deps() {traceback.format_exc()}")

                        deps_not_resolved.add(d)

                deps = rule.deps + rule.sub_rules

                for d in deps:
                    resolve_dep(d)

                for t in rule.tools:
                    resolve_dep(t, is_tool=True)
                    # Bazel provides no indication in its rules that a given rule is a "tool"
                    # We have to infer this based on how it is used - i.e. it exists in another rules list of tools

                deps_resolved[rule.full_path] = rule


        
            resolve_deps(a, 0)

        self.resolve_aliases(deps_log, deps_resolved)

        deps_log.info("resolve_deps() Call rule.resolve() for every rule we need")
        # call resolve for all rules..
        for rule in deps_resolved.values():
            rule.resolve()

        # Now pick out all the rules we need
        deps_log.info("resolve_deps() The full list of resolvable rules is:")
        for path, rule in deps_resolved.items():
            deps_log.info(f"resolve_deps() {path}")

        if len(deps_not_resolved) > 0:
            deps_log.info("resolve_deps() The full list of unresolvable rules is:")
            for a in deps_not_resolved:
                deps_log.info(f"resolve_deps() {a}")
        else:
            deps_log.info("resolve_deps() All dependencies resolved :)")

        dest_dir = Path(output_path)
        self.copy_project_files(dest_dir, deps_resolved)
        tree = self.make_modules_tree()
        self.write_cmake_files(dest_dir, tree, deps_resolved)


    def resolve_aliases(self, deps_log, deps_resolved):

        for name in list(deps_resolved.keys()):
            rule = deps_resolved[name]
            if not isinstance(rule, Project.Module.Alias):
                continue

            deps_log.info(f"Resolving alias : {name}")
            del deps_resolved[name]
            # QDH - really we should resolve these according to the rules set out in the bazel files, but cant be bothered right now.
            actual = None
            match name:
                case "mediapipe/framework/profiler:graph_profiler":
                    actual = self.rule_from_dep_string(rule.module, ":graph_profiler_stub")

                case "third_party:opencv":
                    actual = Project.Module.External("@opencv")

                case "mediapipe/gpu:gpu_shared_data_internal":
                    actual = self.rule_from_dep_string(rule.module, ":gpu_shared_data_internal_actual")

                case "mediapipe/framework/port:threadpool_impl_default_to_google":
                    actual = self.rule_from_dep_string(rule.module, "//mediapipe/framework/deps:threadpool")


                case _:
                    deps_log.info(f"resolve_aliases() IMPLEMENT ME, no resolution for Alias {name}")
                    
            if actual is not None:
                deps_resolved[actual.full_path] = actual
                rule.actual = actual
                deps_log.info(f"resolve_aliases() actual set to {actual.name} for rule {name}")

    def rule_from_dep_string(self, module, str):

        key = None
        try:
            if str.startswith('@'):
                self._log_context.info(f"\tProject.rule_from_dep_string() External dependency: {str}")
                return Project.Module.External(str)

            if ':' in str:
                #self._log_context.info(f"rule_from_dep_string() try to split: {str}")
                (module_path, rule) = str.split(':')
                #self._log_context.info(f"\tProject.rule_from_dep_string() str: \"{str}\", module_path: \"{module_path}\", name: {rule}")
                module = module if module_path == "" else self.get_or_load_module(module_path)
                if module is None:
                    self._log_context.warning("rule_from_dep_string() Module not loaded, cannot find rule!")
                    return None

                if str.startswith("//"):
                    key = str[2:]
                if str.startswith(":"):
                    key = f"{module.path}{str}"


                def resolve_alias(rule):
                    if isinstance(rule, Project.Module.Alias):
                        self._log_context.info(f"\tProject.rule_from_dep_string()::resolve_alias() resolving alias : {rule.name}, actual: {rule.actual}")
                        rule = self.rule_from_dep_string(module, rule.actual)
                    return rule
                
                return resolve_alias(module.rules[key])
    
            self._log_context.warning(f"\tProject.rule_from_dep_string() Implement me! Don't know how to handle dependency: {str}")
        except Exception as e:
             self._log_context.warning(f"\tProject.rule_from_dep_string() Failed for: \"{module.path}\", name: {str}, key: \"{key}\"")
             self._log_context.info(f"\tProject.rule_from_dep_string() module.rules : {module.rules}")
             raise e

    def get_or_load_module(self, module_path):
        #self._log_context.info(f"get_or_load_module() module_path: {module_path}")
        if module_path in self.modules:
            self._log_context.info(f"get_or_load_module() returning existing instance of module with module_path: {module_path}")
            return self.modules[module_path]
        self._log_context.info(f"get_or_load_module() trying to load module with module_path: {module_path}")

        # Each path contains a BUILD file which we parse in the same as we did for top_level_build_file
        module = None
        if module_path.startswith("//"):
            # Absolute path relative to the projects root
            mp = module_path[2:]
            module = Project.Module(self._log_context, mp)

        elif module_path == "":
            # A rule within the same module
            # we shouldn't have been called!
            self._log_context.warning(f"What? why was i called?")
            return None
        else:
            self._log_context.warning(f"No implementation for path: {module_path}")
        
        if module is not None:
            self.modules[module_path] = module
            self._log_context.info(f"get_or_load_module() loaded new module: {module_path}")
        else:
            self._log_context.warning(f"get_or_load_module() failed to load module for : {module_path}")
        return module



    def copy_project_files(self, dest_dir, deps):
        log = self._log_context.new("Write files")
        include_path_dest_dir = dest_dir / include_path
        dest_dir = dest_dir / src_path
        for dep in deps.values():
            if isinstance(dep, Project.Module.AbstractRule):
                dep.copy_files(dest_dir, log)
                dep.copy_files(include_path_dest_dir, log, headers_only=True)


    def make_modules_tree(self):
        '''
        Making the cmake project tree will be a lot easier if our modules objects are themselves
        arranged as a tree....
        '''
        log = self._log_context.new("Make Tree")
        class Dir:
            def __init__(self, parent, name):
                self.parent = parent
                self.name = name
                self.children = {}
                self.module = None


        def get_or_make_dir(d, dir_name):
            if dir_name in d.children:
                return d.children[dir_name]
            new_d = Dir(d, dir_name)
            d.children[dir_name] = new_d
            return new_d

        root = Dir(None, src_path)

        def add_module(module):
            log.info(f"Adding Module: {module.path}")
            cd = root
            path_parts = module.path.split('/')
            for path_part in path_parts:
                cd = get_or_make_dir(cd, path_part)
            if cd.module is not None:
                raise Exception(f"Duplicate module path! {module.path}")
            cd.module = module

        for m in self.modules.values():
            add_module(m)
            

        return root



    def write_cmake_files(self, dest_dir, tree, deps_resolved):
        cmake_log = self._log_context.new("CMake Generator")

        def walk_branch(b, depth):

            write_cmakelists_txt(cmake_log, dest_dir, b, deps_resolved)

            if(len(b.children)):
                cmake_log.info(f"{' '*depth} |")
            for c in b.children.values():
                cmake_log.info(f"{' '*depth} |-> {c.name}, module: {c.module}")
                walk_branch(c, depth+2)

        walk_branch(tree, 0)
            

        tools = ""
        artifacts = ""
        for d in deps_resolved.values():
            if not isinstance(d, Project.Module.AbstractCMakeCompiledRule):
                continue
            if d.is_tool:
                tools += f"{d.cmake_target_name} "
            if d.install:
                artifacts += f"{d.cmake_target_name} "

        content = f'''
cmake_minimum_required(VERSION 3.19)
project(MY_BAZEL_DERIVED_PROJECT)
find_package(Protobuf REQUIRED)
find_package(Eigen3 3.3 REQUIRED)
find_package( OpenCV)
find_package(absl REQUIRED)
find_package(glog REQUIRED)

# Tools needed to build the below
add_custom_target(tools)
# The stuff we actually want
add_custom_target(artifacts)

add_subdirectory(src)
install(TARGETS {tools}DESTINATION bin OPTIONAL)
install(TARGETS {artifacts}DESTINATION lib OPTIONAL)
'''
        content += "INSTALL(DIRECTORY ${CMAKE_SOURCE_DIR}/include  DESTINATION .)\n"


        path = dest_dir / "CMakeLists.txt"
        with path.open("w", encoding ="utf-8") as f:
            f.write(content)






def write_cmakelists_txt(cmake_log, dest_dir, info, deps_resolved):
    '''
    Write the actual CMakeLists.txt file from the info provided in info (Which is an instance of Project::Dir potentially with a Project::Module attached)
    '''
    path = Path()
    cd = info
    while cd is not None:
        path = Path(cd.name) / path
        cd = cd.parent
    path = dest_dir / path
    path.mkdir(parents=True, exist_ok=True)

    path = path / "CMakeLists.txt"

    # The start of our CMakeLists file
    content = ""

    # #Defines
    if info.module:
        definitions = ""
        for _, d in info.module.defines.items():
            for k, v in d.items():
                # QDH
                if k == "use_opencv":
                    v = "false"
                definitions += f"{k}={v} "
        if definitions != "":
            content += f"add_compile_definitions({definitions})\n\n"

    if info.parent is None:
        # This is the CMakeLists.txt that lives in the top level src dir.
        # QDH until figure out how Bazel configures this
        content = "include_directories(. ${OpenCV_INCLUDE_DIRS} ${CMAKE_BINARY_DIR}/src ${CMAKE_SYSROOT}/usr/include/gemmlowp)\n"

        content += "link_directories(${OpenCV_LIB_DIRS})\n\n"

        # Write the protobuf generators which all have to live in this top level CMakeLists.txt
        content += "set(PROTOBUF_IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR})\n"
        content += "set(PROTOBUF_GENERATE_CPP_APPEND_PATH Off)\n\n"


        cmake_log.info(f"Writing protobuf entries....")
        protobufs = []
        for _, rule in deps_resolved.items():
            if not isinstance(rule, Project.Module.CCProtoLibrary):
                #cmake_log.info(f"Ignoring {rule.full_path}")
                continue

            content += rule.cmakelists_content
            protobufs.append(rule.cmake_target_name)

        protobufs = " ".join(protobufs)
        content += f"add_dependencies(artifacts {protobufs})\n"

    tools = ""

    if info.module:
        for rule in info.module.rules.values():
            if isinstance(rule, Project.Module.ConfigSetting):
                continue
            if not rule.required:
                continue

            if isinstance(rule, Project.Module.CCProtoLibrary):
                continue
            if isinstance(rule, Project.Module.AbstractCMakeListsGenerator):
                content += rule.cmakelists_content
            if isinstance(rule, Project.Module.AbstractCMakeCompiledRule):
                if rule.is_tool:
                    tools += f" {rule.cmake_target_name}"
            elif isinstance(rule, Project.Module.MediapipeOptionsLibrary):
                cmake_log.info(f"MediapipeOptionsLibrary is by product of proto_lib: {rule.proto_lib.name}, with the following deps:")
                for d in rule.proto_lib.deps:
                    cmake_log.info(f"   {d}")
            else:
                cmake_log.info(f"IMPLEMENT ME! We need this ({rule.full_path}) no implementation for  {rule.__class__.__name__}")
                

    if len(tools) > 0:
        content += f"add_dependencies(tools {tools})\n"



    for c in info.children:
        content += f"add_subdirectory({c})\n"

    cmake_log.info(f"Writing {path} : {content}")
    with path.open("w", encoding ="utf-8") as f:
        f.write(content)



def run():

    project = Project(top_level_build_path, rules)



def start_logging():
    t = Thread(target=run, args=[])
    t.start()

def main():

    if dpg is None:
        run()

    else:

        dpg.create_context()
        dpg.create_viewport(title='Bazel2Cmake', width=600, height=300)
        
        with dpg.window(label="Window", tag="Window"):
            dpg.add_collapsing_header(label="Log Contexts:", tag="log_context", default_open=True)
            dpg.add_button(label="Start", callback=start_logging)


        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


main()