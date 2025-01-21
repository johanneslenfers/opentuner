import opentuner
from opentuner.search.manipulator import ConfigurationManipulator, InstanceSequenceParameter, IntegerParameter, FloatParameter
from opentuner.measurement.interface import MeasurementInterface

from types import SimpleNamespace

def create_namespace():
    args = SimpleNamespace()
    args.bail_threshold = 500
    args.database = None
    args.display_frequency = 1000000000
    args.generate_bandit_technique = False
    args.label = None
    args.list_techniques = False
    args.machine_class = None
    args.no_dups = False
    args.par = "brr"
    args.parallel_compile = False
    args.parallelism = 4
    args.pipelining = 0
    args.print_params = False
    args.print_search_space_size = False
    args.quiet = True
    args.results_log = None
    args.results_log_details = None
    args.seed_configuration = []
    args.technique = None
    # args.biased = biased 

    # budget 
    args.stop_after = float("inf")
    args.test_limit = 100

    return args


class SequenceTuningExample(MeasurementInterface):
    def manipulator(self):
        """
        Define the configuration manipulator for the tuning problem.
        """
        manipulator = ConfigurationManipulator()

        # Define a fixed alphabet with strings and nested tuning parameters
        alphabet = [
            "loop-unrolling",
            "dead-code-elimination",
            IntegerParameter("tiling", 1, 32),   # Integer tuning parameter
            FloatParameter("beta", 0.0, 1.0),  # Float tuning parameter
            FloatParameter("alpha", 0.0, 1.0),  # Float tuning parameter
            IntegerParameter("parallelize", 1, 32),   # Integer tuning parameter
            IntegerParameter("vectorize", 1, 32),   # Integer tuning parameter
        ]

        # Add a sequence parameter using the alphabet
        sequence_param = InstanceSequenceParameter(
            name="sequence",
            alphabet=alphabet,
            min_length=1,
            max_length=10
        )
        manipulator.add_parameter(sequence_param)

        return manipulator

    def run(self, desired_result, input, limit):
        """
        Evaluate the cost of a configuration.
        """
        config = desired_result.configuration.data  # Access the dictionary representation of the config
        manipulator = self.manipulator()

        # Debug output
        print("\n\n\nConfig before evaluation:", config)

        # Access the sequence parameter
        sequence_param = manipulator.parameters_dict(config)["sequence"]
        sequence = sequence_param.get_value(config)

        print("Evaluating sequence:", sequence)

        # Evaluate the sequence by summing values or assigning scores
        score = 100
        for element in sequence:
            print(f"element: {element}")
            if isinstance(element, int):  # Integer parameter instance
                score += element
                if int(element) % 2 == 0:
                    score += element * (-1)
                else:
                    score += element

            elif isinstance(element, float):  # Float parameter instance
                if float(element) < 0.8 and float(element) > 0.7:
                    score += (element * (-1))
                else:
                    score += element * 10

            elif isinstance(element, str):  # String elements
                if element == "loop-unrolling":
                    score += -1  # Use string length as score
                else:
                    score += -2  # Use string length as score

        print(f"score: {score}")

        return opentuner.resultsdb.models.Result(time=score)

    def save_final_config(self, configuration):
        """
        Save the best configuration found.
        """

        config = configuration.data  # Access the dictionary representation of the config

        sequence_param = self.manipulator().parameters_dict(config)["sequence"]
        sequence = sequence_param.get_value(config)

        print(f"best: ")
        for elem in sequence:
            print(f"    elem: {elem}")


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(parents=opentuner.argparsers())
    # args = parser.parse_args()

    args = create_namespace()
    SequenceTuningExample.main(args)
