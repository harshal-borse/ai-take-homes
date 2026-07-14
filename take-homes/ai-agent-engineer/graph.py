"""LangGraph workflow for Frondly support agent.

This module defines the conversational graph using LangGraph.
The graph orchestrates the agent's decision-making process.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from state import AgentState
from intent_classifier import IntentClassifier
from policy_engine import PolicyEngine
from verification import VerificationManager
from care_advice import CareAdvisor
from escalation import EscalationEngine
from tool_executor import ToolExecutor


class FrondlyAgentGraph:
    """Builds and manages the Frondly agent conversation graph."""
    
    def __init__(self):
        """Initialize the agent graph with all components."""
        self.intent_classifier = IntentClassifier()
        self.policy_engine = PolicyEngine()
        self.verification_manager = VerificationManager()
        self.care_advisor = CareAdvisor()
        self.escalation_engine = EscalationEngine()
        self.tool_executor = ToolExecutor()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("intent_classifier", self._classify_intent)
        workflow.add_node("policy_check", self._check_policy)
        workflow.add_node("verification", self._handle_verification)
        workflow.add_node("tool_execution", self._execute_tools)
        workflow.add_node("response_generation", self._generate_response)
        workflow.add_node("escalation_handling", self._handle_escalation)
        
        # Set entry point
        workflow.set_entry_point("intent_classifier")
        
        # Add edges
        workflow.add_edge("intent_classifier", "policy_check")
        workflow.add_conditional_edges(
            "policy_check",
            self._policy_route,
            {
                "escalation": "escalation_handling",
                "verification": "verification",
                "tools": "tool_execution",
                "care_advice": "response_generation",
                "general": "response_generation"
            }
        )
        workflow.add_edge("verification", "tool_execution")
        workflow.add_edge("tool_execution", "response_generation")
        workflow.add_edge("escalation_handling", "response_generation")
        workflow.add_edge("response_generation", END)
        
        return workflow.compile()
    
    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify the customer's intent.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with intent classification
        """
        message = state.get("customer_message", "")
        intent = self.intent_classifier.classify(message)
        state["intent"] = intent
        return state
    
    def _check_policy(self, state: AgentState) -> AgentState:
        """Check policy compliance and red lines.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with policy decisions
        """
        message = state.get("customer_message", "")
        
        # Check for red lines first
        is_red_line, category = self.policy_engine.check_red_lines(message)
        if is_red_line:
            state["escalation_required"] = True
            state["escalation_category"] = category
            return state
        
        # Check if already escalated
        if self.escalation_engine.is_escalated(state):
            return state
        
        # Check verification requirements
        intent = state.get("intent", "general")
        if self.policy_engine.check_verification_required(intent):
            if not self.verification_manager.check_verification_persistence(state):
                state["intent"] = "verification"
                return state
        
        return state
    
    def _policy_route(self, state: AgentState) -> str:
        """Determine next step based on policy check.
        
        Args:
            state: Current agent state
            
        Returns:
            Route identifier for next node
        """
        # If escalation required
        if state.get("escalation_required", False):
            return "escalation"
        
        # If verification needed
        if state.get("intent") == "verification":
            return "verification"
        
        # If tool execution needed
        if state.get("intent") in ["refund", "subscription", "account_change"]:
            return "tools"
        
        # If care advice
        if state.get("intent") == "care_advice":
            return "care_advice"
        
        # Default to general response
        return "general"
    
    def _handle_verification(self, state: AgentState) -> AgentState:
        """Handle customer verification process.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with verification status
        """
        message = state.get("customer_message", "")
        
        # Extract verification factors
        email = self.verification_manager.extract_email(message)
        order_number = self.verification_manager.extract_order_number(message)
        
        # If we have email, attempt verification
        if email:
            result = self.verification_manager.verify_customer(
                email, order_number
            )
            
            if result["verified"]:
                state["verified"] = True
                state["customer_id"] = result["customer_id"]
                state["email"] = email
                state["verified_via"] = result.get("verified_via")
                state["verified_value"] = result.get("verified_value")
            else:
                # Verification failed - keep state unverified
                state["verification_error"] = result.get("reason", "Verification failed")
        
        return state
    
    def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute appropriate tools based on intent.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with tool execution results
        """
        intent = state.get("intent", "general")
        message = state.get("customer_message", "")
        
        # Route to appropriate tool handler
        if intent == "refund":
            return self._handle_refund(state, message)
        elif intent == "subscription":
            return self._handle_subscription(state, message)
        elif intent == "account_change":
            return self._handle_account_change(state, message)
        
        return state
    
    def _handle_refund(self, state: AgentState, message: str) -> AgentState:
        """Handle refund requests.
        
        Args:
            state: Current agent state
            message: Customer message
            
        Returns:
            Updated state with refund handling results
        """
        # Extract refund details
        customer_id = state.get("customer_id")
        if not customer_id:
            state["error"] = "Customer not verified"
            return state
        
        # In a real implementation, would extract order_id and amount from message
        # For this exercise, use placeholders
        order_id = "ORD-XXXX"  # Would extract from message
        amount = 0.0  # Would extract from message
        reason = message
        
        # Attempt safe refund
        result, error = self.tool_executor.safe_issue_refund(
            customer_id, order_id, amount, reason, state
        )
        
        if error:
            state["error"] = error
            # If error is about ceiling, escalate
            if "ceiling" in error.lower():
                state["escalation_required"] = True
                state["escalation_category"] = "refund_ceiling"
        else:
            state["last_tool_result"] = result
        
        return state
    
    def _handle_subscription(self, state: AgentState, message: str) -> AgentState:
        """Handle subscription changes.
        
        Args:
            state: Current agent state
            message: Customer message
            
        Returns:
            Updated state with subscription handling results
        """
        customer_id = state.get("customer_id")
        if not customer_id:
            state["error"] = "Customer not verified"
            return state
        
        # Determine action from message
        action = "pause"  # Would extract from message
        detail = message
        
        result, error = self.tool_executor.safe_update_subscription(
            customer_id, action, detail, state
        )
        
        if error:
            state["error"] = error
        else:
            state["last_tool_result"] = result
        
        return state
    
    def _handle_account_change(self, state: AgentState, message: str) -> AgentState:
        """Handle account changes.
        
        Args:
            state: Current agent state
            message: Customer message
            
        Returns:
            Updated state with account change handling results
        """
        customer_id = state.get("customer_id")
        if not customer_id:
            state["error"] = "Customer not verified"
            return state
        
        action = "change_address"  # Would extract from message
        detail = message
        
        result, error = self.tool_executor.safe_update_subscription(
            customer_id, action, detail, state
        )
        
        if error:
            state["error"] = error
        else:
            state["last_tool_result"] = result
        
        return state
    
    def _handle_escalation(self, state: AgentState) -> AgentState:
        """Handle escalation creation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with escalation created
        """
        category = state.get("escalation_category", "other")
        member_ref = state.get("customer_id", "unverified caller")
        verification_status = "verified" if state.get("verified") else "unverified"
        
        # Build escalation details
        summary = f"Customer issue requiring escalation: {category}"
        attempted = "Agent attempted to resolve according to policy"
        references = state.get("conversation_id", "")
        customer_facing_line = self.escalation_engine.get_customer_facing_line(category)
        
        # Create escalation
        result, error = self.tool_executor.safe_create_escalation(
            category, member_ref, verification_status, summary,
            attempted, references, customer_facing_line, state
        )
        
        if error:
            state["error"] = error
        else:
            state["last_tool_result"] = result
            # Set escalation latch
            self.escalation_engine.set_escalation_latch(state)
        
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate response to customer.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with response
        """
        # If escalated, use escalation script
        if self.escalation_engine.is_escalated(state):
            state["response"] = self.escalation_engine.get_escalation_response(state)
            return state
        
        # If care advice, provide it
        if state.get("intent") == "care_advice":
            advice = self.care_advisor.get_advice(state.get("customer_message", ""))
            if advice:
                state["response"] = advice
                return state
        
        # If verification failed, request verification
        if state.get("intent") == "verification" and not state.get("verified"):
            state["response"] = "I'd be happy to help! To verify your account, could you please provide your email address along with either your most recent order number or the name of a plant from your latest box?"
            return state
        
        # If there was an error, explain it
        if state.get("error"):
            state["response"] = f"I apologize, but I encountered an issue: {state['error']}"
            return state
        
        # Default response
        state["response"] = "Thank you for reaching out! How can I help you today?"
        return state
    
    def invoke(self, state: AgentState) -> AgentState:
        """Invoke the graph with initial state.
        
        Args:
            state: Initial agent state
            
        Returns:
            Final agent state after graph execution
        """
        return self.graph.invoke(state)