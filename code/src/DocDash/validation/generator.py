import os
import json
import tempfile
from langchain.llms import OpenAI
import pandas as pd
import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.checkpoint import SimpleCheckpoint


class ValidationCodeGenerator:
    def __init__(self, model_name="gpt-4"):
        """Initialize the validation code generator with specified LLM."""
        self.llm = OpenAI(model_name=model_name)

    def generate_validation_code(self, rule_templates):
        """Generate executable Python code for validating data based on rule templates."""
        prompt = f"""
        Create Python code that implements the following validation rules:

        {json.dumps(rule_templates, indent=2)}

        The code should:
        1. Accept a pandas DataFrame as input
        2. Apply each validation rule
        3. Return a dictionary of validation results, including passed/failed status and details for each rule

        Do not use external libraries beyond pandas, numpy, and standard Python libraries.
        Make the code robust to handle edge cases like missing values and different data types.
        """

        validation_code = self.llm(prompt)
        return validation_code

    def generate_pandas_validation(self, rule_templates):
        """Generate pandas-specific validation code."""
        pandas_code_template = """
import pandas as pd
import numpy as np
import json
from datetime import datetime

def validate_data(df):
    \"\"\"
    Validate the input DataFrame against the defined rules.

    Args:
        df (pandas.DataFrame): The data to validate

    Returns:
        dict: Validation results with details on passed/failed rules
    \"\"\"
    results = {
        "summary": {
            "total_rules": 0,
            "passed_rules": 0,
            "failed_rules": 0,
            "validation_timestamp": datetime.now().isoformat()
        },
        "rule_results": {}
    }

    # Make a copy to avoid modifying the original DataFrame
    data = df.copy()

    # Define validation rules
    validation_rules = []

    {rules_definition}

    # Execute validation rules
    for rule in validation_rules:
        rule_id = rule["rule_id"]
        results["summary"]["total_rules"] += 1

        try:
            # Apply the rule's validation function
            rule_result = rule["validation_function"](data)

            # Store the result
            results["rule_results"][rule_id] = {
                "passed": rule_result["passed"],
                "description": rule["description"],
                "severity": rule["severity"]
            }

            # Add details if the rule failed
            if not rule_result["passed"]:
                results["summary"]["failed_rules"] += 1
                results["rule_results"][rule_id]["failed_records"] = rule_result.get("failed_records", [])
                results["rule_results"][rule_id]["error_message"] = rule_result.get("error_message", "")
            else:
                results["summary"]["passed_rules"] += 1

        except Exception as e:
            # Handle exceptions during rule execution
            results["summary"]["failed_rules"] += 1
            results["rule_results"][rule_id] = {
                "passed": False,
                "description": rule["description"],
                "severity": rule["severity"],
                "error_message": f"Error executing rule: {str(e)}"
            }

    return results

if __name__ == "__main__":
    # Example usage
    # df = pd.read_csv("your_data.csv")
    # validation_results = validate_data(df)
    # print(json.dumps(validation_results, indent=2))
    pass
"""

        # Generate rule definitions
        rules_code = []

        for rule in rule_templates:
            rule_id = rule["rule_id"]
            rule_type = rule.get("type", "")
            elements = rule.get("elements", [])
            logic = rule.get("logic", "")
            description = rule.get("description", "")
            severity = rule.get("severity", "warning")

            if not elements:
                continue

            primary_element = elements[0]

            if rule_type == "range_check":
                # Parse range bounds from logic
                lower_bound = "float('-inf')"  # Default
                upper_bound = "float('inf')"  # Default

                if ">=" in logic:
                    lower_bound = logic.split(">=")[1].split("AND")[0].strip()
                if "<=" in logic:
                    upper_bound = logic.split("<=")[1].strip()

                validation_function = f"""
    # Rule {rule_id}: {description}
    validation_rules.append({{
        "rule_id": "{rule_id}",
        "description": "{description}",
        "severity": "{severity}",
        "validation_function": lambda df: {{
            if "{primary_element}" not in df.columns:
                return {{"passed": False, "error_message": "Column {primary_element} not found in DataFrame"}}

            # Find values outside the acceptable range
            mask = ~((df["{primary_element}"] >= {lower_bound}) & (df["{primary_element}"] <= {upper_bound}))
            failed_records = df[mask].index.tolist()

            return {{
                "passed": len(failed_records) == 0,
                "failed_records": failed_records[:100]  # Limit to first 100 for readability
            }}
        }}
    }})
"""
                rules_code.append(validation_function)

            elif rule_type == "categorical_check":
                # Parse valid values from logic
                valid_values = "[]"  # Default

                if "IN" in logic:
                    valid_values = logic.split("IN")[1].strip()

                validation_function = f"""
    # Rule {rule_id}: {description}
    validation_rules.append({{
        "rule_id": "{rule_id}",
        "description": "{description}",
        "severity": "{severity}",
        "validation_function": lambda df: {{
            if "{primary_element}" not in df.columns:
                return {{"passed": False, "error_message": "Column {primary_element} not found in DataFrame"}}

            valid_values = {valid_values}
            # Find values not in the acceptable set
            mask = ~df["{primary_element}"].isin(valid_values)
            failed_records = df[mask].index.tolist()

            return {{
                "passed": len(failed_records) == 0,
                "failed_records": failed_records[:100]  # Limit to first 100 for readability
            }}
        }}
    }})
"""
                rules_code.append(validation_function)

            elif rule_type == "not_null_check":
                validation_function = f"""
    # Rule {rule_id}: {description}
    validation_rules.append({{
        "rule_id": "{rule_id}",
        "description": "{description}",
        "severity": "{severity}",
        "validation_function": lambda df: {{
            if "{primary_element}" not in df.columns:
                return {{"passed": False, "error_message": "Column {primary_element} not found in DataFrame"}}

            # Find null values
            mask = df["{primary_element}"].isna()
            failed_records = df[mask].index.tolist()

            return {{
                "passed": len(failed_records) == 0,
                "failed_records": failed_records[:100]  # Limit to first 100 for readability
            }}
        }}
    }})
"""
                rules_code.append(validation_function)

            elif rule_type == "cross_field_check" and len(elements) >= 2:
                # More complex handling for cross-field validations
                secondary_element = elements[1]

                # Default cross-field check is equality
                validation_function = f"""
    # Rule {rule_id}: {description}
    validation_rules.append({{
        "rule_id": "{rule_id}",
        "description": "{description}",
        "severity": "{severity}",
        "validation_function": lambda df: {{
            if "{primary_element}" not in df.columns or "{secondary_element}" not in df.columns:
                missing_cols = [col for col in ["{primary_element}", "{secondary_element}"] if col not in df.columns]
                return {{"passed": False, "error_message": f"Columns {{missing_cols}} not found in DataFrame"}}

            # Find records where the cross-field validation fails
            # This is a simplified check - customize based on the specific logic
            mask = df["{primary_element}"] != df["{secondary_element}"]
            failed_records = df[mask].index.tolist()

            return {{
                "passed": len(failed_records) == 0,
                "failed_records": failed_records[:100]  # Limit to first 100 for readability
            }}
        }}
    }})
"""
                rules_code.append(validation_function)

        # Complete the template with the rules
        complete_code = pandas_code_template.format(rules_definition="\n".join(rules_code))
        return complete_code

    def execute_validation_on_data(self, validation_code, data):
        """Execute the generated validation code on the provided data."""
        # Write the validation code to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
            tmp.write(validation_code.encode('utf-8'))
            tmp_path = tmp.name

        try:
            # Import the validation module
            import importlib.util
            spec = importlib.util.spec_from_file_location("validation_module", tmp_path)
            validation_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validation_module)

            # Execute validation
            results = validation_module.validate_data(data)
            return results
        finally:
            # Clean up the temporary file
            os.unlink(tmp_path)

    def execute_great_expectations_validation(self, data, suite_name, dataset_name):
        """Run Great Expectations validation on the data using the specified suite."""
        context = ge.data_context.DataContext()

        # Convert data to a Pandas DataFrame if it's not already
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)

        # Create a batch request
        batch_request = RuntimeBatchRequest(
            datasource_name="my_datasource",
            data_connector_name="default_runtime_data_connector_name",
            data_asset_name=dataset_name,
            runtime_parameters={"batch_data": data},
            batch_identifiers={"default_identifier_name": "default_identifier"},
        )

        # Create checkpoint config
        checkpoint_config = {
            "name": f"{dataset_name}_checkpoint",
            "config_version": 1.0,
            "class_name": "SimpleCheckpoint",
            "run_name_template": "%Y%m%d-%H%M%S-validation",
        }

        # Create and run the checkpoint
        checkpoint = SimpleCheckpoint(
            name=checkpoint_config["name"],
            data_context=context,
            config_version=checkpoint_config["config_version"],
            run_name_template=checkpoint_config["run_name_template"],
        )

        results = checkpoint.run(
            validations=[
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": suite_name,
                }
            ]
        )

        return results
