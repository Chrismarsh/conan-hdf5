import os
import shutil
from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanException


class ConfigurationException(Exception):
    pass


class Hdf5Conan(ConanFile):
    name = "hdf5"

    description = "HDF5 C and C++ libraries"
    license = "https://support.hdfgroup.org/ftp/HDF5/releases/COPYING"
    settings = "os", "compiler", "build_type", "arch"
    
    options = {
        "cxx": [True, False],
        "shared": [True, False],
        "parallel": [True, False]
    }
    default_options = (
        "cxx=True",
        "shared=True",
        "parallel=False",
        "zlib:shared=False"
    )
    generators = "virtualbuildenv"
    source_subfolder = "hdf5"

    def requirements(self):
        self.requires("zlib/[>=1.2]")


    def configure(self):
        if self.options.cxx and self.options.parallel:
            msg = "The cxx and parallel options are not compatible"
            raise ConfigurationException(msg)


    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        os.rename("hdf5-{0}".format(self.version), self.source_subfolder)

        if tools.os_info.is_macos and self.options.shared:
            tools.replace_in_file("%s/configure" % self.source_subfolder, r"-install_name \$rpath/", "-install_name @rpath/")


    def build(self):
        configure_args = [
            "--prefix=" + self.package_folder,
            "--enable-hl",
            "--disable-sharedlib-rpath"
        ]

        if self.settings.build_type == "Debug":
            configure_args.append("--enable-build-mode=debug")

        if self.options.cxx:
            configure_args.append("--enable-cxx")

        if self.options.shared:
            configure_args.append("--enable-shared")
            configure_args.append("--disable-static")
        else:
            configure_args.append("--disable-shared")
            configure_args.append("--enable-static")

        if self.options.parallel:
            if os.environ.get("CC") is None:
                os.environ["CC"] = os.environ.get("MPICC", "mpicc")
            if os.environ.get("CXX") is None:
                os.environ["CXX"] = os.environ.get("MPICXX", "mpic++")
            configure_args.append("--enable-parallel")

        if tools.os_info.is_linux and self.options.shared:
            val = os.environ.get("LDFLAGS", "")
            os.environ["LDFLAGS"] = val + " -Wl,-rpath='$$ORIGIN/../lib'"

        env_build = AutoToolsBuildEnvironment(self)
        env_build.configure(
            configure_dir=self.source_subfolder,
            args=configure_args
        )

        env_build.make()

        env_build.make(args=["install"])

        # The paths in the HDF5 compiler wrapper are hard-coded, so
        # substitute the prefix by a variable named H5CC_PREFIX to be
        # passed to it. The compiler wrapper can be called h5cc or h5pcc.
        if self.options.parallel:
            hdf5_compiler_wrapper = os.path.join(self.package_folder, "bin", "h5pcc")
        else:
            hdf5_compiler_wrapper = os.path.join(self.package_folder, "bin", "h5cc")

        try:
            tools.replace_in_file(
                hdf5_compiler_wrapper,
                'prefix=""',
                'prefix="$(cd "$( dirname "$0" )" && pwd)/.."'
            )
        except:
            pass # don't need the patch in later versions

        if tools.os_info.is_macos and self.options.shared:
            self._add_rpath_to_executables(os.path.join(self.package_folder, "bin"))

    def _add_rpath_to_executables(self, path):
        executables = [
            "gif2h5", "h52gif", "h5clear", "h5copy", "h5debug", "h5diff",
            "h5dump", "h5format_convert", "h5import", "h5jam", "h5ls",
            "h5mkgrp", "h5perf_serial", "h5repack", "h5repart", "h5stat",
            "h5unjam", "h5watch"
        ]
        cwd = os.getcwd()
        os.chdir(path)
        for e in executables:
            cmd = "install_name_tool -add_rpath {0} {1}".format(
                "@executable_path/../lib", e
            )
            os.system(cmd)

        os.chdir(cwd)

    def package(self):
        self.copy("*", dst="bin", src="install/bin")
        self.copy("*", dst="include", src="install/include")
        self.copy("*", dst="lib", src="install/lib")
        self.copy("LICENSE.*", src=self.source_subfolder)
        self.copy("CHANGES.*", src=self.source_subfolder)

    def package_info(self):
        self.cpp_info.libs = ["hdf5", "hdf5_hl"]
        if self.options.cxx:
            self.cpp_info.libs.append("hdf5_cpp")
        if tools.os_info.is_windows:
            self.cpp_info.defines = ["H5_BUILT_AS_DYNAMIC_LIB"]
