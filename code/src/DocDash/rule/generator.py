import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import great_expectations as ge
from langchain.llms import OpenAI


class RuleGenerator:
    def __init__(self, model_name="gpt-4"):
        """Initialize the rule generator with specified LLM."""
        self.llm = OpenAI(model_name=model_name)

    def generate_rule_templates(self, refined_requirements):
        """Generate rule templates based on refined requirements."""
        prompt = f"""
        Convert the following refined data validation requirements into rule templates
        that can be used to generate executable validation code:

        {refined_requirements}

        For each rule, provide:
        1. A unique rule ID
        2. The data element(s) involved
        3. The validation logic in pseudocode
        4. The type of validation (e.g., range check, cross-field validation, etc.)
        5. The severity level if the rule is violated (e.g., error, warning, info)

        Return the rule templates in a structured JSON format.
        """

        rule_templates = self.llm(prompt)
        return json.loads(rule_templates)

    def discover_rules_from_data(self, data, sample_size=10000):
        """Discover additional rules based on unsupervised learning from sample data."""
        # Convert to DataFrame if not already
        if not isinstance(data, pd.DataFrame):
            data = pd.DataFrame(data)

        # Sample data if it's large
        if len(data) > sample_size:
            data_sample = data.sample(sample_size, random_state=42)
        else:
            data_sample = data

        discovered_rules = []

        # 1. Statistical distribution rules for numeric columns
        numeric_cols = data_sample.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Skip columns with too many missing values
            if data_sample[col].isna().sum() / len(data_sample) > 0.5:
                continue

            values = data_sample[col].dropna()

            # Outlier detection using IQR
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            discovered_rules.append({
                "rule_id": f"auto_range_{col}",
                "elements": [col],
                "logic": f"{col} >= {lower_bound} AND {col} <= {upper_bound}",
                "type": "range_check",
                "severity": "warning",
                "confidence": "medium",
                "description": f"Value of {col} should typically be between {lower_bound:.2f} and {upper_bound:.2f}"
            })

        # 2. Categorical value rules
        categorical_cols = data_sample.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            # Skip columns with too many unique values
            if data_sample[col].nunique() > 20:
                continue

            value_counts = data_sample[col].value_counts(normalize=True)
            common_values = value_counts[value_counts > 0.01].index.tolist()

            discovered_rules.append({
                "rule_id": f"auto_categorical_{col}",
                "elements": [col],
                "logic": f"{col} IN {common_values}",
                "type": "categorical_check",
                "severity": "warning",
                "confidence": "medium",
                "description": f"{col} typically contains one of these values: {', '.join(map(str, common_values))}"
            })

        # 3. Discover potential correlations between columns
        correlation_matrix = data_sample.select_dtypes(include=[np.number]).corr().abs()

        # Get pairs of columns with high correlation
        corr_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i):
                if correlation_matrix.iloc[i, j] > 0.8:  # Threshold for high correlation
                    col1 = correlation_matrix.columns[i]
                    col2 = correlation_matrix.columns[j]
                    corr_pairs.append((col1, col2, correlation_matrix.iloc[i, j]))

        for col1, col2, corr_value in corr_pairs:
            discovered_rules.append({
                "rule_id": f"auto_correlation_{col1}_{col2}",
                "elements": [col1, col2],
                "logic": f"Correlation between {col1} and {col2}",
                "type": "correlation_check",
                "severity": "info",
                "confidence": "low",
                "description": f"{col1} and {col2} appear to be correlated (correlation: {corr_value:.2f})"
            })

        return discovered_rules

    def create_great_expectations_suite(self, rule_templates, dataset_name):
        """Create a Great Expectations suite from rule templates."""
        context = ge.data_context.DataContext()
        suite = context.create_expectation_suite(
            expectation_suite_name=f"{dataset_name}_suite",
            overwrite_existing=True
        )

        for rule in rule_templates:
            rule_type = rule.get("type", "")
            elements = rule.get("elements", [])

            if not elements:
                continue

            primary_element = elements[0]

            if rule_type == "range_check":
                # Extract bounds from logic
                logic = rule.get("logic", "")
                # Simple parsing for demonstration purposes
                lower_bound = float('-inf')
                upper_bound = float('inf')

                if ">=" in logic:
                    lower_bound = float(logic.split(">=")[1].split("AND")[0].strip())
                if "<=" in logic:
                    upper_bound = float(logic.split("<=")[1].strip())

                suite.add_expectation(
                    ge.core.expectation_configuration.ExpectationConfiguration(
                        expectation_type="expect_column_values_to_be_between",
                        kwargs={
                            "column": primary_element,
                            "min_value": lower_bound,
                            "max_value": upper_bound
                        }
                    )
                )

            elif rule_type == "categorical_check":
                # Extract valid values from logic
                logic = rule.get("logic", "")
                # Simple parsing for demonstration purposes
                if "IN" in logic:
                    valid_values = logic.split("IN")[1].strip()
                    valid_values = json.loads(valid_values.replace("'", "\""))

                    suite.add_expectation(
                        ge.core.expectation_configuration.ExpectationConfiguration(
                            expectation_type="expect_column_values_to_be_in_set",
                            kwargs={
                                "column": primary_element,
                                "value_set": valid_values
                            }
                        )
                    )

            elif rule_type == "not_null_check":
                suite.add_expectation(
                    ge.core.expectation_configuration.ExpectationConfiguration(
                        expectation_type="expect_column_values_to_not_be_null",
                        kwargs={
                            "column": primary_element
                        }
                    )
                )

        context.save_expectation_suite(suite)
        return suite
