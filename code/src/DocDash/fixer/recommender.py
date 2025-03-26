import pandas as pd
import json
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import logging


class RemediationRecommender:
    def __init__(self, model_name="gpt-4"):
        """Initialize the remediation recommender with specified LLM."""
        self.llm = OpenAI(model_name=model_name)
        self.logger = logging.getLogger(__name__)

    def generate_remediation_recommendations(self, validation_results, data, rule_templates):
        """Generate remediation recommendations for failed validations."""
        recommendations = {
            "summary": {
                "total_issues": 0,
                "remediated_issues": 0,
                "manual_review_issues": 0
            },
            "remediation_plans": {}
        }

        # If no rule results, return empty recommendations
        if "rule_results" not in validation_results:
            return recommendations

        failed_rules = [
            rule_id for rule_id, result in validation_results["rule_results"].items()
            if not result.get("passed", True)
        ]

        recommendations["summary"]["total_issues"] = len(failed_rules)

        # If no failed rules, return empty recommendations
        if not failed_rules:
            return recommendations

        # Get rule details from templates
        rule_details = {
            rule["rule_id"]: rule for rule in rule_templates
            if rule["rule_id"] in failed_rules
        }

        # Process each failed rule
        for rule_id in failed_rules:
            rule_result = validation_results["rule_results"].get(rule_id, {})
            rule_info = rule_details.get(rule_id, {})

            # Get failed records
            failed_indices = rule_result.get("failed_records", [])
            if not failed_indices:
                continue

            # Get sample of failed data
            failed_data = data.loc[failed_indices[:10]].to_dict(orient='records')

            # Generate remediation plan
            remediation_plan = self._generate_single_remediation(
                rule_id, rule_info, rule_result, failed_data
            )

            # Categorize the remediation
            if remediation_plan["can_automate"]:
                recommendations["summary"]["remediated_issues"] += 1
            else:
                recommendations["summary"]["manual_review_issues"] += 1

            recommendations["remediation_plans"][rule_id] = remediation_plan

        return recommendations

    def _generate_single_remediation(self, rule_id, rule_info, rule_result, failed_data):
        """Generate remediation plan for a single failed rule."""
        # Prepare the prompt for the LLM
        prompt_template = PromptTemplate(
            input_variables=["rule_id", "rule_info", "failed_data", "rule_result"],
            template="""
            Generate a remediation plan for the following validation issue:

            Rule ID: {rule_id}
            Rule Type: {rule_info[type]}
            Rule Description: {rule_info[description]}
            Severity: {rule_info[severity]}

            The validation failed on these example records:
            {failed_data}

            Based on this information, please provide:
            1. A concise explanation of why the data likely failed this validation
            2. Step-by-step remediation actions that could be taken
            3. Whether this could be remediated automatically (true/false)
            4. If automatic remediation is possible, provide pseudocode for the fix
            5. A suggested explanation for auditors about this issue

            Format your response as a JSON object with the following structure:
            ```
            {{
                "explanation": "Clear explanation of the issue",
                "remediation_steps": ["Step 1", "Step 2", "..."],
                "can_automate": true/false,
                "automation_code": "Pseudocode or actual code for fixing the issue",
                "auditor_explanation": "Explanation suitable for auditors"
            }}
            ```
            """
        )

        # Format the prompt
        formatted_prompt = prompt_template.format(
            rule_id=rule_id,
            rule_info=rule_info,
            failed_data=json.dumps(failed_data, indent=2),
            rule_result=json.dumps(rule_result, indent=2)
        )

        try:
            # Get remediation plan from LLM
            llm_response = self.llm(formatted_prompt)

            # Parse JSON response
            # Extract JSON from the response if it's wrapped in backticks
            json_str = llm_response
            if "```" in llm_response:
                json_str = llm_response.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()

            remediation_plan = json.loads(json_str)

            # Validate the structure
            required_keys = ["explanation", "remediation_steps", "can_automate", "auditor_explanation"]
            for key in required_keys:
                if key not in remediation_plan:
                    remediation_plan[key] = "Not provided"

            # Add metadata
            remediation_plan["rule_id"] = rule_id
            remediation_plan["rule_type"] = rule_info.get("type", "unknown")
            remediation_plan["severity"] = rule_info.get("severity", "unknown")

            return remediation_plan

        except Exception as e:
            self.logger.error(f"Error generating remediation for rule {rule_id}: {str(e)}")
            # Return a fallback plan
            return {
                "rule_id": rule_id,
                "rule_type": rule_info.get("type", "unknown"),
                "severity": rule_info.get("severity", "unknown"),
                "explanation": "Could not generate explanation due to an error.",
                "remediation_steps": ["Manual review required"],
                "can_automate": False,
                "automation_code": "N/A",
                "auditor_explanation": "Validation failed, but automatic remediation recommendation could not be generated. Manual review required."
            }

    def apply_automatic_remediations(self, data, remediation_plans):
        """Apply automatic remediations to the data where possible."""
        remediated_data = data.copy()
        applied_remediations = []

        for rule_id, plan in remediation_plans.items():
            if not plan.get("can_automate", False):
                continue

            try:
                # Convert the automation code to executable Python
                # This is just a placeholder - in practice, you'd need a more sophisticated approach
                automation_prompt = f"""
                Convert the following remediation pseudocode to executable Python code 
                that can be applied to a pandas DataFrame named 'df':

                {plan.get('automation_code', '')}

                The code should:
                1. Accept a pandas DataFrame as input
                2. Apply the remediation logic
                3. Return the modified DataFrame
                4. Include appropriate error handling

                Return only the Python function definition.
                """

                code = self.llm(automation_prompt)

                # Create a function from the code
                local_vars = {}
                exec(code, globals(), local_vars)

                # Find the function in local_vars
                remediation_func = None
                for func in local_vars.values():
                    if callable(func):
                        remediation_func = func
                        break

                if remediation_func:
                    # Apply the remediation
                    remediated_data = remediation_func(remediated_data)
                    applied_remediations.append({
                        "rule_id": rule_id,
                        "status": "applied",
                        "description": plan.get("explanation", "")
                    })
                else:
                    applied_remediations.append({
                        "rule_id": rule_id,
                        "status": "failed",
                        "error": "Could not extract remediation function from code"
                    })

            except Exception as e:
                applied_remediations.append({
                    "rule_id": rule_id,
                    "status": "failed",
                    "error": str(e)
                })

        return remediated_data, applied_remediations

    def generate_audit_report(self, validation_results, remediation_plans, applied_remediations):
        """Generate a comprehensive audit report for documentation purposes."""
        # Prepare data for the report
        report_data = {
            "validation_summary": validation_results.get("summary", {}),
            "remediation_summary": {
                "total_issues": len(remediation_plans),
                "automated_remediations": len([p for p in applied_remediations if p["status"] == "applied"]),
                "failed_remediations": len([p for p in applied_remediations if p["status"] == "failed"]),
                "manual_review_required": len(
                    [p for p in remediation_plans.values() if not p.get("can_automate", False)])
            },
            "issue_details": []
        }

        # Add details for each issue
        for rule_id, plan in remediation_plans.items():
            rule_result = validation_results.get("rule_results", {}).get(rule_id, {})

            # Find if remediation was applied
            remediation_status = "not_attempted"
            remediation_error = None

            for rem in applied_remediations:
                if rem["rule_id"] == rule_id:
                    remediation_status = rem["status"]
                    if remediation_status == "failed":
                        remediation_error = rem.get("error", "Unknown error")

            # Add to report
            report_data["issue_details"].append({
                "rule_id": rule_id,
                "description": plan.get("explanation", ""),
                "severity": plan.get("severity", "unknown"),
                "remediation_steps": plan.get("remediation_steps", []),
                "automated": plan.get("can_automate", False),
                "remediation_status": remediation_status,
                "remediation_error": remediation_error,
                "auditor_explanation": plan.get("auditor_explanation", "")
            })

        # Generate the report using LLM
        report_prompt = f"""
        Generate a comprehensive audit report based on the following validation and remediation information:

        {json.dumps(report_data, indent=2)}

        The report should include:
        1. An executive summary
        2. Validation results overview
        3. Remediation actions taken
        4. Issues requiring manual review
        5. Recommendations for process improvement

        Format the report as a well-structured markdown document with appropriate headings, lists, and formatting.
        """

        audit_report = self.llm(report_prompt)
        return audit_report
