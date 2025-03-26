import os
import json
import pandas as pd
import logging
from datetime import datetime


class AIDataProfilerOrchestrator:
    def __init__(self, instruction_processor, rule_generator, validation_code_generator, remediation_recommender):
        """Initialize the orchestrator with its component classes."""
        self.instruction_processor = instruction_processor
        self.rule_generator = rule_generator
        self.validation_code_generator = validation_code_generator
        self.remediation_recommender = remediation_recommender

        # Configure logging
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Initialize state variables
        self.regulatory_docs = []
        self.data_sources = []
        self.extracted_requirements = None
        self.refined_requirements = None
        self.rule_templates = None
        self.discovered_rules = None
        self.validation_code = None
        self.validation_results = None
        self.remediation_plans = None

    def add_regulatory_document(self, document_path):
        """Add a regulatory document to be processed."""
        if os.path.exists(document_path):
            self.regulatory_docs.append(document_path)
            self.logger.info(f"Added regulatory document: {document_path}")
        else:
            self.logger.error(f"Document not found: {document_path}")

    def add_data_source(self, data_path=None, dataframe=None):
        """Add a data source to be profiled and validated."""
        if data_path and os.path.exists(data_path):
            self.data_sources.append({"type": "file", "path": data_path})
            self.logger.info(f"Added data source file: {data_path}")
        elif dataframe is not None:
            self.data_sources.append({"type": "dataframe", "data": dataframe})
            self.logger.info(f"Added DataFrame data source with {len(dataframe)} rows")
        else:
            self.logger.error("No valid data source provided")

    def process_regulatory_documents(self):
        """Process regulatory documents to extract validation requirements."""
        if not self.regulatory_docs:
            self.logger.warning("No regulatory documents added")
            return None

        self.logger.info("Processing regulatory documents...")
        self.instruction_processor.process_documents(self.regulatory_docs)

        self.extracted_requirements = self.instruction_processor.extract_validation_requirements()
        self.logger.info("Requirements extracted successfully")

        self.refined_requirements = self.instruction_processor.refine_requirements(self.extracted_requirements)
        self.logger.info("Requirements refined successfully")

        return self.refined_requirements

    def generate_validation_rules(self, data_sample=None):
        """Generate validation rules based on requirements and data samples."""
        if not self.refined_requirements:
            self.logger.warning("No refined requirements available. Please process regulatory documents first.")
            return None

        self.logger.info("Generating rule templates from regulatory requirements...")
        self.rule_templates = self.rule_generator.generate_rule_templates(self.refined_requirements)

        if data_sample is not None:
            self.logger.info("Discovering additional rules from data sample...")
            self.discovered_rules = self.rule_generator.discover_rules_from_data(data_sample)

            # Combine template-based rules with discovered rules
            self.rule_templates.extend(self.discovered_rules)
            self.logger.info(f"Combined {len(self.rule_templates)} total rules")

        return self.rule_templates

    def generate_validation_code(self):
        """Generate executable validation code based on rule templates."""
        if not self.rule_templates:
            self.logger.warning("No rule templates available. Please generate validation rules first.")
            return None

        self.logger.info("Generating validation code...")
        self.validation_code = self.validation_code_generator.generate_pandas_validation(self.rule_templates)
        self.logger.info("Validation code generated successfully")

        return self.validation_code

    def validate_data(self, data=None):
        """Validate data against the generated rules."""
        if data is None and not self.data_sources:
            self.logger.warning("No data sources available for validation")
            return None

        if not self.validation_code:
            self.logger.warning("No validation code available. Please generate validation code first.")
            return None

        # Use the provided data or the first data source
        df = None
        if data is not None:
            df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        else:
            source = self.data_sources[0]
            if source["type"] == "file":
                df = pd.read_csv(source["path"])
            else:
                df = source["data"].copy()

        self.logger.info(f"Validating data with {len(df)} rows...")
        self.validation_results = self.validation_code_generator.execute_validation_on_data(
            self.validation_code, df
        )

        self.logger.info("Validation completed")
        summary = self.validation_results.get("summary", {})
        self.logger.info(f"Validation summary: {summary}")

        return self.validation_results

    def generate_remediation_plans(self, data=None):
        """Generate remediation plans for validation issues."""
        if not self.validation_results:
            self.logger.warning("No validation results available. Please validate data first.")
            return None

        if not self.rule_templates:
            self.logger.warning("No rule templates available. Required for remediation planning.")
            return None

        # Use the provided data or the first data source
        df = None
        if data is not None:
            df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        else:
            source = self.data_sources[0]
            if source["type"] == "file":
                df = pd.read_csv(source["path"])
            else:
                df = source["data"].copy()

        self.logger.info("Generating remediation plans...")
        self.remediation_plans = self.remediation_recommender.generate_remediation_recommendations(
            self.validation_results, df, self.rule_templates
        )

        self.logger.info("Remediation plans generated")
        summary = self.remediation_plans.get("summary", {})
        self.logger.info(f"Remediation summary: {summary}")

        return self.remediation_plans

    def apply_remediations(self, data=None):
        """Apply automatic remediations to the data."""
        if not self.remediation_plans:
            self.logger.warning("No remediation plans available. Please generate remediation plans first.")
            return None, []

        # Use the provided data or the first data source
        df = None
        if data is not None:
            df = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        else:
            source = self.data_sources[0]
            if source["type"] == "file":
                df = pd.read_csv(source["path"])
            else:
                df = source["data"].copy()

        self.logger.info("Applying automatic remediations...")
        remediated_data, applied_remediations = self.remediation_recommender.apply_automatic_remediations(
            df, self.remediation_plans.get("remediation_plans", {})
        )

        self.logger.info(f"Applied {len([r for r in applied_remediations if r['status'] == 'applied'])} remediations")

        return remediated_data, applied_remediations

    def generate_audit_report(self, applied_remediations=None):
        """Generate a comprehensive audit report."""
        if not self.validation_results or not self.remediation_plans:
            self.logger.warning("Missing validation results or remediation plans. Required for audit report.")
            return None

        self.logger.info("Generating audit report...")
        audit_report = self.remediation_recommender.generate_audit_report(
            self.validation_results,
            self.remediation_plans.get("remediation_plans", {}),
            applied_remediations or []
        )

        self.logger.info("Audit report generated successfully")

        return audit_report

    def run_end_to_end_pipeline(self, data=None, generate_report=True):
        """Run the complete end-to-end pipeline."""
        self.logger.info("Starting end-to-end pipeline...")

        # Step 1: Process regulatory documents
        self.process_regulatory_documents()

        # Step 2: Generate validation rules
        if data is not None:
            sample_size = min(10000, len(data))
            data_sample = data.sample(sample_size) if hasattr(data, 'sample') else data[:sample_size]
            self.generate_validation_rules(data_sample)
        else:
            self.generate_validation_rules()

        # Step 3: Generate validation code
        self.generate_validation_code()

        # Step 4: Validate data
        self.validate_data(data)

        # Step 5: Generate remediation plans
        self.generate_remediation_plans(data)

        # Step 6: Apply remediations
        remediated_data, applied_remediations = self.apply_remediations(data)

        # Step 7: Generate audit report if requested
        audit_report = None
        if generate_report:
            audit_report = self.generate_audit_report(applied_remediations)

        self.logger.info("End-to-end pipeline completed successfully")

        return {
            "remediated_data": remediated_data,
            "validation_results": self.validation_results,
            "remediation_plans": self.remediation_plans,
            "applied_remediations": applied_remediations,
            "audit_report": audit_report
        }

    def save_results(self, output_dir):
        """Save all results to files in the specified directory."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save rule templates
        if self.rule_templates:
            with open(os.path.join(output_dir, f"rule_templates_{timestamp}.json"), 'w') as f:
                json.dump(self.rule_templates, f, indent=2)

        # Save validation code
        if self.validation_code:
            with open(os.path.join(output_dir, f"validation_code_{timestamp}.py"), 'w') as f:
                f.write(self.validation_code)

        # Save validation results
        if self.validation_results:
            with open(os.path.join(output_dir, f"validation_results_{timestamp}.json"), 'w') as f:
                json.dump(self.validation_results, f, indent=2)

        # Save remediation plans
        if self.remediation_plans:
            with open(os.path.join(output_dir, f"remediation_plans_{timestamp}.json"), 'w') as f:
                json.dump(self.remediation_plans, f, indent=2)

        self.logger.info(f"Results saved to {output_dir}")
