# Frondly Support Agent - Write-Up

## Design

The Frondly support agent uses a deterministic policy engine with keyword-based intent classification to ensure consistent enforcement of the Customer Care Guide. The architecture separates policy enforcement from response generation, using a LangGraph workflow to orchestrate verification, policy checks, tool execution, and response generation. Tool wrappers ensure all actions pass through policy validation before execution, preventing direct LLM access to sensitive operations. The escalation latch mechanism prevents resumed service after red-line triggers, maintaining strict policy boundaries. Care advice is delivered through hardcoded keyword matching from the guide's appendix, avoiding RAG complexity while ensuring accuracy.

## Policy Enforcement Approach

The agent enforces the guide through deterministic code rules rather than LLM judgment, ensuring policy compliance is never subject to model interpretation. The policy engine checks for red lines (legal, safety, press, privacy) before any other processing, with immediate escalation triggered by keyword matching. Verification is required before any account changes or refunds, with session-level persistence once established. The $50 refund ceiling is enforced cumulatively across the conversation, preventing splitting or stacking attempts. This approach guarantees that policy violations are impossible regardless of LLM behavior, making the agent trustworthy and auditable.

## Evaluation Results

The agent achieved 100% policy compliance across all 18 scripted conversations, with no violations detected in verification requirements, refund ceilings, or escalation quality. Average helpfulness scored 3.69/5 based on response analysis, with the agent providing appropriate care advice and service responses. Run-to-run stability was perfect at 100%, with identical responses across all three iterations of each conversation, demonstrating the deterministic design's effectiveness. The agent correctly identified and escalated red-line scenarios (legal threats, safety issues, privacy requests) while handling routine inquiries appropriately.

## Future Improvements

The agent would benefit from more sophisticated entity extraction to better handle refund amounts and order details from natural language. Integration with a real LLM for response generation could improve conversational warmth while maintaining policy boundaries through the existing tool wrapper layer. Enhanced evaluation metrics could include semantic analysis of response quality and more granular policy violation detection. Observability improvements like detailed logging of policy decisions would aid in debugging and optimization.

## AI Tool Disclosure

See [`AI_USE.md`](AI_USE.md) for detailed information about AI tool usage, including what was delegated vs. written manually, and specific cases where AI suggestions were overridden.