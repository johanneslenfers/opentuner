import subprocess
from types import SimpleNamespace
import opentuner
import re
from opentuner.measurement import MeasurementInterface
from opentuner.search.manipulator import ConfigurationManipulator, EnumParameter

def create_namespace():
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
        parallelism=4,
        pipelining=0,
        print_params=False,
        print_search_space_size=False,
        quiet=True,
        results_log=None,
        results_log_details=None,
        seed_configuration=[],
        technique=None,
        stop_after=float("inf"),
        test_limit=500
    )

class LLVMOpentunerTuning(MeasurementInterface):
    """Class for tuning LLVM optimization passes using OpenTuner."""

    def get_available_passes(self):
    # """Retrieve a list of available LLVM passes and dynamically parse their parameters."""
        print("get passes")
        try:
            # Execute the opt command to get passes
            result = subprocess.run(["opt", "--print-passes"], text=True, capture_output=True, check=True)
            lines = result.stdout.split("\n")

            passes = {}
            for line in lines:
                # process line 
                # Extract the pass name and any parameters (if present)
                if "  " in line:  # Matches lines with pass names
                    if "<" in line:
                        pattern = r"<([^>]+)>"

                        # Find all matches
                        params = str(re.findall(pattern, line)[0]).split(";")
                        # print(f"     params: {params}")

                        pass_name= line.split("<")[0].strip()

                        for param in params:
                            self.test_pass(param)

                        passes[pass_name] = params

                    else:
                        parts = line.split()
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
           

            # remove all passes that start with print

            keys_to_delete = []
            for key in passes:
                if "print" in key:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                print(f"delete: {key}")
                del passes[key]

            return passes
        except subprocess.CalledProcessError as e:
            print(f"Error executing 'opt --print-passes': {e.stderr}")
            return {}


    def get_parameterized_passes(self):
        """Generate a list of parameterized LLVM passes dynamically."""
        passes_with_params = self.get_available_passes()
        parameterized_passes = []

        for pass_name, params in passes_with_params.items():
            if params:
                for param in params:
                    if "=N" in param:
                        # Replace =N with a concrete value
                        parameterized_passes.append(f"{pass_name}<{param.replace('=N', '=32')}>")
                    else:
                        parameterized_passes.append(f"{pass_name}<{param}>")
            else:
                parameterized_passes.append(pass_name)

        # test all and remove 
        # think about invalid parameters 
        # parameterized_passes = list(filter(lambda c_pass: self.test_pass(c_pass), parameterized_passes))

        return parameterized_passes


    def manipulator(self):
        """Define the configuration space."""
        manipulator = ConfigurationManipulator()
        available_passes = self.get_parameterized_passes()

        if not available_passes:
            raise RuntimeError("No LLVM passes found. Ensure LLVM is installed and accessible.")

        for i in range(20):  # Tune up to 10 passes in sequence
            manipulator.add_parameter(EnumParameter(f"pass{i}", available_passes))
        return manipulator

    def run(self, desired_result, input, limit):
        """Compile, optimize, and benchmark the program based on the configuration."""
        config = desired_result.configuration.data
        passes = list(config.values())

        try:
            self.compile_program("algorithm.c", "algorithm.ll")
            self.apply_passes(passes, "algorithm.ll", "optimized_algorithm.bc")
            self.compile_to_object("optimized_algorithm.bc", "algorithm.o")
            self.compile_c_to_object("host.c", "host.o")
            self.link_objects(["algorithm.o", "host.o"], "benchmark")
            execution_time = self.run_benchmark("benchmark")

            print(f"pass: {config.values()}")
            print(f"runtime: {execution_time}")
            # import sys
            # sys.exit(0)

            return opentuner.resultsdb.models.Result(time=execution_time)
        except subprocess.CalledProcessError as e:
            print(f"Error during compilation or execution: {e.stderr}")
            return opentuner.resultsdb.models.Result(time=float(2**31 - 1))

    def test_pass(self, compiler_pass)-> bool:
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


    def compile_program(self, source, output):
        """Compile a source file to LLVM IR."""
        self.run_command(["clang", "-S", "-emit-llvm", source, "-o", output])

    def apply_passes(self, passes, input_ir, output_ir):
        """Apply LLVM passes to the input IR."""
        pass_pipeline = ",".join(passes)
        test = ["opt"] + [f"-passes={pass_pipeline}"] + [input_ir, "-o", output_ir]
        print(" ".join(test))
        if passes:
            self.run_command(["opt"] + [f"-passes={pass_pipeline}"] + [input_ir, "-o", output_ir])
        else:
            self.run_command(["cp", input_ir, output_ir])

    def compile_to_object(self, input_file, output_file):
        """Compile LLVM IR or source file to object code."""
        self.run_command(["llc", "-filetype=obj", input_file, "-o", output_file])

    def compile_c_to_object(self, input_file, output_file):
        """Compile LLVM IR or source file to object code."""
        self.run_command(["clang", "-c", input_file, "-o", output_file])

    def link_objects(self, objects, output):
        """Link object files into an executable."""
        self.run_command(["clang"] + objects + ["-o", output])

    def run_benchmark(self, executable):
        """Run the benchmark and return execution time."""
        result = self.run_command(["./" + executable])
        return self.parse_execution_time(result.stdout)

    def run_command(self, command):
        """Run a shell command and return the result."""
        return subprocess.run(command, text=True, capture_output=True, check=True)

    def parse_execution_time(self, output):
        """Parse execution time from program output."""
        try:
            for line in output.split("\n"):
                if "Time:" in line:
                    return float(line.split(":")[1].strip())
        except Exception as e:
            print(f"Error parsing execution time: {e}")
        return float("inf")  # Return a large value on failure

if __name__ == "__main__":
    args = create_namespace()
    # LLVMOpentunerTuning.main(args)
    # argparser = opentuner.default_argparser()
    # argparser.add_argument(--database=my_tuning_results.db)
    LLVMOpentunerTuning.main(args)
