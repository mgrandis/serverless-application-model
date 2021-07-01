import copy
import json
import os.path
from parameterized import parameterized
import pytest
from unittest import TestCase
from samtranslator.yaml_helper import yaml_parse
from samtranslator.validator.validator import SamTemplateValidator
from tests.validator.test_validator import TestValidatorBase, TestValidatorProvider

BASE_PATH = os.path.dirname(__file__)
INPUT_FOLDER = os.path.join(BASE_PATH, "input")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "output")


class TestValidatorGlobals(TestValidatorBase):
    @parameterized.expand(
        [
            ("AccessLogSetting", "error_accesslogsetting"),
            ("Auth", "error_auth"),
            ("Auth", "error_auth_cognito"),
            ("Auth", "error_auth_cognito"),
            ("Auth", "error_auth_lambda"),
            ("Auth", "error_auth_lambdarequest_identity"),
            ("Auth", "error_auth_lambdatoken_identity"),
            ("Auth", "error_auth_resourcepolicy"),
            ("Auth", "error_auth_usageplan"),
            ("BinaryMediaTypes", "error_binarymediatypes"),
            # ("CacheCluster", "error_cachecluster"),  # This needs to be cut in two files
            ("CanarySetting", "error_canarysetting"),
            ("Cors", "error_cors"),
            ("DefinitionUri", "error_definitionuri"),
            ("Domain", "error_domain"),
            ("EndpointConfiguration", "error_endpointconfiguration"),
            ("GatewayResponses", "error_gatewayresponses"),
            ("MethodSettings", "error_methodsettings"),
            ("MinimumCompressionSize", "error_minimumcompressionsize"),
            ("Name", "error_name"),
            ("OpenApiVersion", "error_openapiversion"),
            ("TracingEnabled", "error_tracingenabled"),
            ("Variables", "error_variables"),
        ],
    )
    def test_errors_api(self, property_name, resource_error_file):
        self._test_validator_error_globals("api", "Api", property_name, "error_api", resource_error_file)

    # @parameterized.expand(
    #     [
    #         "success_auth_cognito",
    #         "success_auth_lambdarequest",
    #         "success_complete_api",
    #         "success_minimal_api",
    #     ],
    # )
    # def test_success_api(self, template):
    #     self._test_validator_success(os.path.join(INPUT_FOLDER, template))

    def _test_validator_error_globals(
        self, resource_test_dir, resource_name, property_name, base_input_file, resource_test_file
    ):
        """
        Tests the Globals property using the tests already written for the Resource.
        This ensures we validate both with the same tests without having to rewrite them.

        Parameters
        ----------
        resource_test_dir : str
            Input test file sub directory
        resource_name : str
            Name of the resource under the Globals property
        property_name : str
            Name of the Resource property to test
        base_input_file : str
            Name of the input file to use as base to build the test case file
        resource_test_file : str
            Name of the input/output file for the Resource test
        """
        globals_result = self._get_globals_test_result(
            resource_test_dir, resource_name, property_name, base_input_file, resource_test_file
        )
        resource_output_test_content = self._get_expected_test_result(
            resource_test_dir, resource_name, property_name, resource_test_file
        )

        self.assertEqual(resource_output_test_content, globals_result)

    def _get_globals_test_result(
        self, resource_test_dir, resource_name, property_name, base_input_file, resource_test_file
    ):
        """
        Fetches the tests cases from the input test file and,
        for each, builds a corresponding Globals test case
        using base_input_file and runs the Validator on it.

        Returns a list of all errors combined, sorted.

        Parameters
        ----------
        resource_test_dir : str
            [description]
        resource_name : str
            [description]
        property_name : str
            [description]
        base_input_file : str
            [description]
        resource_test_file : str
            [description]

        Returns
        -------
        List[str]
            List of errors
        """
        resource_input_file_path = os.path.join(INPUT_FOLDER, resource_test_dir, resource_test_file + ".yaml")
        base_input_file_path = os.path.join(INPUT_FOLDER, "globals", base_input_file + ".yaml")

        # Get the cases to test
        values_to_test = []
        with open(resource_input_file_path) as f:
            resource_input_file_dict = yaml_parse(f.read())
            for _, value in resource_input_file_dict["Resources"].items():
                values_to_test.append(value["Properties"][property_name])

        # Get the base test file content
        with open(base_input_file_path) as f:
            base_input_file_dict = yaml_parse(f.read())

        # Run the tests and collect the results
        globals_result = []

        for value in values_to_test:
            work_dict = copy.deepcopy(base_input_file_dict)
            work_dict["Globals"][resource_name] = {}
            work_dict["Globals"][resource_name][property_name] = value

            validator = TestValidatorProvider.get()
            validation_errors = validator.validate(work_dict)
            globals_result = globals_result + validation_errors

        return sorted(globals_result)

    def _get_expected_test_result(self, resource_test_dir, resource_name, property_name, resource_test_file):
        """
        Gets the expected test results from the error file
        and transforms their error path to be relative to
        the Globals path to ease comparison with the errors
        from the validator

        Example:
        [Resources/ApiAccessLogSettingDestinationArnNotString/Properties/AccessLogSetting/DestinationArn] 3 is not of type 'string', 'intrinsic'
        -->
        [Globals/Api/AccessLogSetting/DestinationArn] 3 is not of type 'string', 'intrinsic'

        Parameters
        ----------
        resource_test_dir : str
            [description]
        resource_name : str
            [description]
        property_name : str
            [description]
        resource_test_file : str
            [description]

        Returns
        -------
        List[str]
            List of errors
        """
        resource_output_file_path = os.path.join(OUTPUT_FOLDER, resource_test_dir, resource_test_file + ".json")

        with open(resource_output_file_path) as f:
            resource_output_test_content = json.loads(f.read())

        for i, msg in enumerate(resource_output_test_content):
            msg_items = msg.split("/" + property_name)
            resource_output_test_content[i] = "[Globals/" + resource_name + "/" + property_name + msg_items[1]

        return sorted(resource_output_test_content)