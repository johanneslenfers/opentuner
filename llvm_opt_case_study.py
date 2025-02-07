import subprocess
from subprocess import CompletedProcess
from types import SimpleNamespace
import opentuner
import re
from opentuner.measurement import MeasurementInterface
from opentuner.search.manipulator import ConfigurationManipulator, EnumParameter

LENGTH: int = 5

# FIX_COMPILER_OPTIONS: list[str] = ['-mavx2', '-mfma', '-march=native']
FIX_COMPILER_OPTIONS: list[str] = []

def create_namespace() -> SimpleNamespace:
    """Create and return a namespace for custom arguments."""
    return SimpleNamespace(
        bail_threshold=500,
        database="llvm.db",
        display_frequency=1000000000,
        generate_bandit_technique=False,
        label=None,
        list_techniques=False,
        machine_class=None,
        no_dups=False,
        par="brr",
        parallel_compile=False,
        parallelism=12,
        pipelining=0,
        print_params=False,
        print_search_space_size=False,
        quiet=True,
        results_log=None,
        results_log_details=None,
        seed_configuration=[],
        technique=None,
        stop_after=float("inf"),
        test_limit=100
    )

# TODO: verify that we do not miss on a good path there 
passes_to_avoid: list[str] = [
    "dot-callgraph",
    "print",
    "print-callgraph",
    "print-callgraph-sccs",
    "print-ir-similarity",
    "print-lcg",
    "print-lcg-dot",
    "print-must-be-executed-contexts",
    "print-profile-summary",
    "print-stack-safety",
    "view-callgraph",
    "callgraph",
    "dot-cfg",
    "dot-cfg-only",
    "dot-dom",
    "dot-dom-only",
    "dot-post-dom",
    "dot-post-dom-only",
    "flatten-cfg",
    "print-alias-sets",
    "print-cfg-sccs",
    "print-memderefs",
    "print-mustexecute",
    "print-predicateinfo",
    "structurizecfg",
    "view-cfg",
    "view-cfg-only",
    "cfguard",
    "simplifycfg",
    "dot-ddg",
    "loop-simplifycfg",
]


class LLVMOpentunerTuning(MeasurementInterface):
    """Class for tuning LLVM optimization passes using OpenTuner."""
    def get_available_passes(self) -> dict[str, list[str]]:
    # """Retrieve a list of available LLVM passes and dynamically parse their parameters."""
        try:
            # Execute the opt command to get passes
            result: CompletedProcess[str] = subprocess.run(["opt", "--print-passes"], text=True, capture_output=True, check=True)
            lines: list[str] = result.stdout.split("\n")

            # TODO: clean this up 
            passes: dict[str, list[str]] = {}
            for line in lines:
                # process line 
                # Extract the pass name and any parameters (if present)
                if "  " in line:  # Matches lines with pass names
                    if "<" in line:
                        pattern = r"<([^>]+)>"

                        # Find all matches
                        params: list[str] = str(re.findall(pattern, line)[0]).split(";")

                        pass_name: str = line.split("<")[0].strip()

                        # this is for checking parameterized configs, right? 
                        # for param in params:
                        #     self.test_pass(param)

                        passes[pass_name] = params

                    else:
                        parts: list[str] = line.split()
                        pass_name = parts[0]
                        passes[pass_name] = []

            #     print(line)
            
            # # Prepare storage for passes and their parameters
            # passes = {}
            # skip = False
            # for line in lines:
            #     print(f"line: {line}")
            #     stripped = line.strip()
            #     if not stripped:
            #         continue  # Skip empty lines

            #     # print(f"line: {line}")

            #     # test passes 

            #     # skip function analyses passes
            #     if line == "Function analyses:" or line == "Function alias analyses:" or line == "Machine function analyses (WIP):" or line == "Module analyses:" or line == "Module alias analyses:":
            #         print(f"skip: ")
            #         # skip if we have this category
            #         skip = True
            #         continue
            #     elif "  " in line:
            #         # if we have a value within this category, skip
            #         if skip:
            #             print(f"    dont add: {line}")
            #             continue
            #     else:
            #         # if we get a new value, skip 
            #         print(f"    end this: {line}")
            #         skip = False
                
            #     # Extract the pass name and any parameters (if present)
            #     if "  " in line:  # Matches lines with pass names
            #         if "<" in line:
            #             pattern = r"<([^>]+)>"

            #             # Find all matches
            #             params = str(re.findall(pattern, line)[0]).split(";")
            #             # print(f"     params: {params}")

            #             pass_name= line.split("<")[0].strip()
            #             passes[pass_name] = params
 
            #         else:
            #             parts = line.split()
            #             pass_name = parts[0]
            #             passes[pass_name] = []
           

            # TODO make this better 
            keys_to_delete: list[str] = []
            for key in passes:
                if "print" in key:
                    keys_to_delete.append(key)
                
                elif "dot" in key:
                    keys_to_delete.append(key)

                elif "callgraph" in key:
                    keys_to_delete.append(key)

                elif "cfg" in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                # print(f"delete: {key}")
                del passes[key]
            
            return passes

        except subprocess.CalledProcessError as e:
            print(f"Error executing 'opt --print-passes': {e.stderr}")
            return {}


    def get_parameterized_passes(self) -> list[str]:
        """Generate a list of parameterized LLVM passes dynamically."""
        passes_with_params: dict[str, list[str]] = self.get_available_passes()
        parameterized_passes: list[str] = []

        for pass_name, params in passes_with_params.items():
            if params:
                for param in params:
                    if "=N" in param:
                        # Replace =N with a concrete value
                        parameterized_passes.append(f"{pass_name}<{param.replace('=N', '=32')}>")
                    else:
                        parameterized_passes.append(f"{pass_name}<{param}>")
            else:
                if "dot" not in pass_name:
                    parameterized_passes.append(pass_name)
                else:
                    print(f"pass_name: {pass_name}")

        # test only a single pass is difficult as they interact 
        # we have to consider the whole sequence 
        # Check if we filter out too much? 
        # parameterized_passes = list(filter(lambda c_pass: self.test_pass(c_pass), parameterized_passes))

        # add dummy/empty pass
        parameterized_passes.append("dummy")

        return parameterized_passes


    def manipulator(self) -> ConfigurationManipulator:
        """Define the configuration space."""

        # TODO: fix default config. Opentuner seems to mutate the initial config at the beginning. 
        # seed config 
        seed_config = {
            "pass0": "dummy",
            "pass1": "dummy",
        }

        # manipulator = ConfigurationManipulator(seed_config=seed_config)
        manipulator = ConfigurationManipulator()
        available_passes: list[str] = self.get_parameterized_passes()

        # think about 
        # initial_config = manipulator.seed_config()
        # for elem in initial_config:
        #     print(f"{elem}: {initial_config[elem]}")

        if not available_passes:
            raise RuntimeError("No LLVM passes found. Ensure LLVM is installed and accessible.")

        # create sequence
        for i in range(LENGTH):  
            manipulator.add_parameter(EnumParameter(f"pass{i}", available_passes)) # type: ignore

        # print(manipulator.seed_config())
        manipulator._seed_config = seed_config

        return manipulator

    def run(self, desired_result, input, limit):
        """Compile, optimize, and benchmark the program based on the configuration."""
        config = desired_result.configuration.data
        passes: list[str] = list(config.values())

        # filter out empty passes 
        passes2: list[str] = [cpass for cpass in passes if "dummy" not in cpass]

        passes = passes2

        try:
            self.compile_program("algorithm.c", "algorithm.ll")
            self.apply_passes(passes, "algorithm.ll", "optimized_algorithm.bc")
            self.compile_to_object("optimized_algorithm.bc", "algorithm.o")
            self.compile_c_to_object("host.c", "host.o")
            self.link_objects(["algorithm.o", "host.o"], "benchmark")
            execution_time: float = self.run_benchmark("benchmark")

            print(f"pass: {config.values()}") # type: ignore
            print(f"runtime: {execution_time}")
            # import sys
            # sys.exit(0)

            return opentuner.resultsdb.models.Result(time=execution_time) # type: ignore
        except subprocess.CalledProcessError as e:
            print(f"Error during compilation or execution: {e.stderr}")
            return opentuner.resultsdb.models.Result(time=float(2**31 - 1)) # type: ignore

    def test_pass(self, compiler_pass: str)-> bool:
        try:
            self.compile_program("algorithm.c", "algorithm.ll")
            self.apply_passes([compiler_pass], "algorithm.ll", "optimized_algorithm.bc")
            self.compile_to_object("optimized_algorithm.bc", "algorithm.o")
            self.compile_c_to_object("host.c", "host.o")
            self.link_objects(["algorithm.o", "host.o"], "benchmark")

            print("valid")
            return True
        except:
            print("invalid")
            return False


    def compile_program(self, source: str, output: str) -> None:
        """Compile a source file to LLVM IR."""
        self.run_command(["clang", '-O0'] + FIX_COMPILER_OPTIONS + ["-S", "-emit-llvm", source, "-o", output]) # type: ignore


    def apply_passes(self, passes: list[str], input_ir: str, output_ir: str) -> None:
        """Apply LLVM passes to the input IR."""
        pass_pipeline = ",".join(passes)
        test = ["opt"] + [f"-passes={pass_pipeline}"] + [input_ir, "-o", output_ir]
        print(" ".join(test))
        if passes:
            self.run_command(["opt"] + [f"-passes={pass_pipeline}"] + [input_ir, "-o", output_ir]) # type: ignore
        else: 
            self.run_command(["cp", input_ir, output_ir]) # type: ignore

    def compile_to_object(self, input_file: str, output_file: str) -> None:
        """Compile LLVM IR or source file to object code."""
        self.run_command(["llc", "-filetype=obj", input_file, "-o", output_file]) # type: ignore

    def compile_c_to_object(self, input_file: str, output_file: str) -> None:
        """Compile LLVM IR or source file to object code."""
        self.run_command(["clang", "-c", input_file, "-o", output_file]) # type: ignore

    def link_objects(self, objects: list[str], output: str) -> None:
        """Link object files into an executable."""
        self.run_command(["clang"] + FIX_COMPILER_OPTIONS + objects + ["-o", output]) # type: ignore

    def run_benchmark(self, executable: str) -> float:
        """Run the benchmark and return execution time."""
        result: CompletedProcess[str] = self.run_command(["./" + executable]) # type: ignore
        return self.parse_execution_time(result.stdout)

    def run_command(self, command: list[str]) -> CompletedProcess[str]:
        """Run a shell command and return the result."""
        return subprocess.run(command, text=True, capture_output=True, check=True)

    def parse_execution_time(self, output: str) -> float:
        """Parse execution time from program output."""
        try:
            for line in output.split("\n"):
                if "Median Time:" in line:
                    return float(line.split(":")[1].strip())
        except Exception as e:
            print(f"Error parsing execution time: {e}")
        return float("inf")  # Return a large value on failure

if __name__ == "__main__":

    # remove llvm.db before running a new experiment 
    # save existing one or store result afterwards 
    command: list[str] = ['rm', 'llvm.db']
    subprocess.run(command, text=True, capture_output=True, check=False)

    args = create_namespace()
    # LLVMOpentunerTuning.main(args)
    # argparser = opentuner.default_argparser()
    # argparser.add_argument(--database=my_tuning_results.db)
    LLVMOpentunerTuning.main(args) # type: ignore
