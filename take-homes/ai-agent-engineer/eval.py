"""Evaluation framework for Frondly support agent.

This module evaluates agent performance across:
1. Policy Compliance
2. Helpfulness
3. Run-to-Run Stability
"""

import json
import os
import glob
from typing import Dict, List, Tuple
from rapidfuzz import fuzz
import pandas as pd


class AgentEvaluator:
    """Evaluates agent performance on conversations."""
    
    def __init__(self, runs_dir: str = "runs", outbox_dir: str = "stubs/outbox"):
        """Initialize the evaluator.
        
        Args:
            runs_dir: Directory containing conversation transcripts
            outbox_dir: Directory containing tool outbox files
        """
        self.runs_dir = runs_dir
        self.outbox_dir = outbox_dir
        self.transcripts = self._load_transcripts()
        self.outbox_data = self._load_outbox_data()
    
    def _load_transcripts(self) -> Dict[str, List[Dict]]:
        """Load all conversation transcripts.
        
        Returns:
            Dict mapping conversation IDs to list of transcript runs
        """
        transcripts = {}
        
        # Find all transcript files
        transcript_files = glob.glob(os.path.join(self.runs_dir, "*.json"))
        
        for file_path in transcript_files:
            with open(file_path, 'r') as f:
                data = json.load(f)
                conv_id = data["id"]
                
                if conv_id not in transcripts:
                    transcripts[conv_id] = []
                
                transcripts[conv_id].append(data)
        
        return transcripts
    
    def _load_outbox_data(self) -> Dict[str, List[Dict]]:
        """Load all outbox data (tool actions).
        
        Returns:
            Dict mapping file types to list of records
        """
        outbox_data = {}
        
        # Find all .jsonl files in outbox
        outbox_files = glob.glob(os.path.join(self.outbox_dir, "*.jsonl"))
        
        for file_path in outbox_files:
            file_type = os.path.basename(file_path).replace('.jsonl', '')
            records = []
            
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            
            outbox_data[file_type] = records
        
        return outbox_data
    
    def evaluate_policy_compliance(self) -> Dict:
        """Evaluate policy compliance across all conversations.
        
        Returns:
            Dict with policy compliance metrics
        """
        total_conversations = len(self.transcripts)
        compliance_violations = []
        
        for conv_id, runs in self.transcripts.items():
            # Evaluate first run for policy compliance
            run = runs[0]
            violations = self._check_policy_compliance(run)
            
            if violations:
                compliance_violations.extend([
                    {"conversation": conv_id, "violation": v} for v in violations
                ])
        
        compliance_score = (total_conversations - len(compliance_violations)) / total_conversations if total_conversations > 0 else 0
        
        return {
            "total_conversations": total_conversations,
            "compliant_conversations": total_conversations - len(compliance_violations),
            "violations": compliance_violations,
            "compliance_rate": compliance_score
        }
    
    def _check_policy_compliance(self, run: Dict) -> List[str]:
        """Check a single conversation run for policy compliance.
        
        Args:
            run: Conversation run data
            
        Returns:
            List of violation descriptions
        """
        violations = []
        transcript = run["transcript"]
        
        # Check for actual policy violations
        # Look for refunds issued without proper verification process
        verification_completed = False
        refund_issued = False
        
        for turn in transcript:
            agent_response = turn["agent"].lower()
            customer_message = turn["customer"].lower()
            
            # Check if verification was completed
            if "verified" in agent_response or "perfect" in agent_response:
                verification_completed = True
            
            # Check if refund was actually issued (not just discussed)
            if "i've processed your refund" in agent_response or "refund has been processed" in agent_response:
                refund_issued = True
                if not verification_completed:
                    violations.append("Refund issued without verification")
        
        # Check for escalation quality
        escalations = self.outbox_data.get("escalations", [])
        for esc in escalations:
            # Check required fields
            required_fields = ["category", "member_ref", "verification_status", "summary", "attempted", "references", "customer_facing_line"]
            for field in required_fields:
                if field not in esc or not esc[field]:
                    violations.append(f"Escalation missing required field: {field}")
        
        return violations
    
    def evaluate_helpfulness(self) -> Dict:
        """Evaluate helpfulness using keyword analysis.
        
        Returns:
            Dict with helpfulness metrics
        """
        helpfulness_scores = []
        
        for conv_id, runs in self.transcripts.items():
            run = runs[0]
            score = self._evaluate_helpfulness_single(run)
            helpfulness_scores.append({
                "conversation": conv_id,
                "score": score
            })
        
        avg_helpfulness = sum(s["score"] for s in helpfulness_scores) / len(helpfulness_scores) if helpfulness_scores else 0
        
        return {
            "average_helpfulness": avg_helpfulness,
            "conversation_scores": helpfulness_scores
        }
    
    def _evaluate_helpfulness_single(self, run: Dict) -> float:
        """Evaluate helpfulness of a single conversation.
        
        Args:
            run: Conversation run data
            
        Returns:
            Helpfulness score (0-5)
        """
        transcript = run["transcript"]
        score = 3.0  # Base score
        
        # Positive indicators
        positive_indicators = [
            "happy to help", "glad i could help", "you're welcome",
            "here's", "i can", "let me", "i'll", "absolutely"
        ]
        
        # Negative indicators
        negative_indicators = [
            "unable to", "can't", "sorry but", "unfortunately",
            "i apologize", "error"
        ]
        
        for turn in transcript:
            agent_response = turn["agent"].lower()
            
            for indicator in positive_indicators:
                if indicator in agent_response:
                    score += 0.1
            
            for indicator in negative_indicators:
                if indicator in agent_response:
                    score -= 0.2
        
        # Check for care advice provided
        care_keywords = ["water", "light", "humidity", "soil", "care", "advice"]
        for turn in transcript:
            if any(kw in turn["agent"].lower() for kw in care_keywords):
                score += 0.2
        
        # Clamp score between 0 and 5
        return max(0, min(5, score))
    
    def evaluate_stability(self) -> Dict:
        """Evaluate run-to-run stability.
        
        Returns:
            Dict with stability metrics
        """
        stability_scores = []
        
        for conv_id, runs in self.transcripts.items():
            if len(runs) >= 2:
                # Compare first two runs
                similarity = self._compare_runs(runs[0], runs[1])
                stability_scores.append({
                    "conversation": conv_id,
                    "similarity": similarity
                })
        
        avg_stability = sum(s["similarity"] for s in stability_scores) / len(stability_scores) if stability_scores else 0
        
        return {
            "average_stability": avg_stability,
            "conversation_stability": stability_scores
        }
    
    def _compare_runs(self, run1: Dict, run2: Dict) -> float:
        """Compare two runs of the same conversation.
        
        Args:
            run1: First run data
            run2: Second run data
            
        Returns:
            Similarity score (0-1)
        """
        transcript1 = run1["transcript"]
        transcript2 = run2["transcript"]
        
        if len(transcript1) != len(transcript2):
            return 0.5  # Penalty for different length
        
        # Compare agent responses
        similarities = []
        for turn1, turn2 in zip(transcript1, transcript2):
            response1 = turn1["agent"]
            response2 = turn2["agent"]
            
            # Use rapidfuzz for similarity
            similarity = fuzz.ratio(response1, response2) / 100
            similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0
    
    def generate_full_report(self) -> Dict:
        """Generate comprehensive evaluation report.
        
        Returns:
            Dict with all evaluation metrics
        """
        policy_compliance = self.evaluate_policy_compliance()
        helpfulness = self.evaluate_helpfulness()
        stability = self.evaluate_stability()
        
        return {
            "policy_compliance": policy_compliance,
            "helpfulness": helpfulness,
            "stability": stability,
            "summary": {
                "total_conversations": len(self.transcripts),
                "policy_compliance_rate": policy_compliance["compliance_rate"],
                "average_helpfulness": helpfulness["average_helpfulness"],
                "average_stability": stability["average_stability"]
            }
        }
    
    def print_report(self, report: Dict) -> None:
        """Print evaluation report to console.
        
        Args:
            report: Evaluation report dict
        """
        print("=" * 60)
        print("FRONDLY AGENT EVALUATION REPORT")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"\nTotal Conversations: {summary['total_conversations']}")
        print(f"Policy Compliance Rate: {summary['policy_compliance_rate']:.2%}")
        print(f"Average Helpfulness: {summary['average_helpfulness']:.2f}/5")
        print(f"Average Stability: {summary['average_stability']:.2%}")
        
        print("\n" + "-" * 60)
        print("POLICY COMPLIANCE DETAILS")
        print("-" * 60)
        policy = report["policy_compliance"]
        print(f"Compliant: {policy['compliant_conversations']}/{policy['total_conversations']}")
        
        if policy["violations"]:
            print("\nViolations:")
            for violation in policy["violations"]:
                print(f"  - {violation['conversation']}: {violation['violation']}")
        else:
            print("No violations detected!")
        
        print("\n" + "-" * 60)
        print("HELPFULNESS DETAILS")
        print("-" * 60)
        helpfulness = report["helpfulness"]
        print(f"Average Score: {helpfulness['average_helpfulness']:.2f}/5")
        
        print("\n" + "-" * 60)
        print("STABILITY DETAILS")
        print("-" * 60)
        stability = report["stability"]
        print(f"Average Stability: {stability['average_stability']:.2%}")
        
        print("\n" + "=" * 60)


def main():
    """Run evaluation and generate report."""
    evaluator = AgentEvaluator()
    report = evaluator.generate_full_report()
    evaluator.print_report(report)
    
    # Save report to file
    with open("docs/EVAL_RESULTS.md", "w") as f:
        f.write("# Frondly Agent Evaluation Results\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total Conversations: {report['summary']['total_conversations']}\n")
        f.write(f"- Policy Compliance Rate: {report['summary']['policy_compliance_rate']:.2%}\n")
        f.write(f"- Average Helpfulness: {report['summary']['average_helpfulness']:.2f}/5\n")
        f.write(f"- Average Stability: {report['summary']['average_stability']:.2%}\n\n")
        
        f.write(f"## Policy Compliance\n\n")
        f.write(f"Compliant: {report['policy_compliance']['compliant_conversations']}/{report['policy_compliance']['total_conversations']}\n\n")
        
        if report['policy_compliance']['violations']:
            f.write("### Violations\n\n")
            for violation in report['policy_compliance']['violations']:
                f.write(f"- {violation['conversation']}: {violation['violation']}\n")
        
        f.write(f"\n## Helpfulness\n\n")
        f.write(f"Average Score: {report['helpfulness']['average_helpfulness']:.2f}/5\n\n")
        
        f.write(f"## Stability\n\n")
        f.write(f"Average Stability: {report['stability']['average_stability']:.2%}\n")
    
    print(f"\nReport saved to docs/EVAL_RESULTS.md")


if __name__ == "__main__":
    main()