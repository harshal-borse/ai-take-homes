# Frondly Support Agent - Design Document

## Architecture Overview

The Frondly support agent is built using a deterministic policy engine with LangGraph workflow orchestration. The architecture prioritizes policy compliance over conversational flexibility, ensuring that the Customer Care Guide is enforced through code rather than LLM judgment.

## Core Components

### 1. State Management (`state.py`)
- **AgentState**: TypedDict defining conversation state including verification status, escalation latch, refund tracking, and intent classification
- Session persistence ensures verification and escalation status maintain across conversation turns

### 2. Policy Engine (`policy_engine.py`)
- **Deterministic Rules**: All policy decisions made through keyword matching and logical checks
- **Red Line Detection**: Immediate escalation for legal, safety, press, privacy concerns
- **Refund Ceiling Enforcement**: $50 cumulative limit per conversation, never bypassed
- **Verification Requirements**: Account changes and refunds require verified identity
- **No LLM Policy Decisions**: LLM never determines policy compliance

### 3. Intent Classifier (`intent_classifier.py`)
- **Keyword-Based Classification**: Simple pattern matching for stability
- **Categories**: refund, subscription, account_change, care_advice, shipping, legal, safety, press, privacy, general
- **Deterministic Output**: Same message always produces same classification

### 4. Verification Manager (`verification.py`)
- **Multi-Factor Verification**: Email + order number OR plant name
- **Session Persistence**: Verification status maintained once established
- **Customer Lookup**: Integration with provided customer data
- **Order Validation**: Verifies against recent order history

### 5. Care Advisor (`care_advice.py`)
- **Hardcoded Knowledge**: Customer Care Guide Appendix §9
- **Keyword Matching**: No RAG or vector database required
- **Topics**: Yellow leaves, brown tips, leggy growth, fungus gnats, spider mites, repotting, watering, light
- **Deterministic Responses**: Same question always gets same advice

### 6. Escalation Engine (`escalation.py`)
- **Escalation Latch**: Once escalated, never resume normal service
- **Required Fields**: Category, member reference, verification status, summary, attempted actions, references, customer-facing line
- **Scripted Responses**: Pre-written escalation scripts for each category
- **Audit Trail**: All escalations recorded to outbox

### 7. Tool Executor (`tool_executor.py`)
- **Policy Wrappers**: All tool execution passes through policy checks
- **Safe Operations**: Never expose tools directly to LLM
- **Verification Gates**: Protected operations require verified session
- **Ceiling Enforcement**: Refund operations check cumulative total
- **Error Handling**: Policy violations return clear error messages

### 8. LangGraph Workflow (`graph.py`)
- **State Graph**: Orchestrates conversation flow through nodes
- **Nodes**: intent_classifier, policy_check, verification, tool_execution, response_generation, escalation_handling
- **Conditional Routing**: Policy decisions determine next steps
- **Deterministic Flow**: Same state always produces same path

### 9. Main Agent (`agent.py`)
- **respond() Function**: Harness-compatible interface
- **Session Management**: Initializes and maintains conversation state
- **Message Processing**: Routes through workflow based on intent and policy
- **Response Generation**: Contextual responses based on conversation state

## Policy Enforcement Strategy

### Verification First
- No account changes or refunds without verification
- Verification requires email + order number OR plant name
- Verification persists for conversation duration
- Third-party requests (husband, roommate) always denied

### Red Line Escalation
- Legal threats trigger immediate escalation
- Safety/ingestion issues trigger immediate escalation with referral scripts
- Privacy requests trigger immediate escalation
- Press/influencer inquiries routed appropriately
- Once escalated, conversation never returns to normal service

### Refund Policy
- $50 cumulative ceiling per conversation
- No splitting, stacking, or creative recategorization
- COA claims require photo within 14 days
- Policy reasons only (crispy, damaged, shipping issues)
- Verification required before any refund

### Tool Safety
- All tools wrapped with policy checks
- LLM never directly executes tools
- Each operation validates session state
- Audit trail recorded in outbox

## Data Flow

1. **Customer Message** → Intent Classifier
2. **Intent** → Policy Engine (Red Line Check)
3. **Policy Decision** → Route (Escalation/Verification/Tools/General)
4. **If Verification Needed** → Extract factors → Verify customer
5. **If Tools Needed** → Policy check → Execute wrapped tool
6. **If Escalation** → Build escalation → Set latch
7. **Response Generation** → Contextual response based on state

## Stability Guarantees

- **Deterministic Policy**: Same inputs always produce same policy decisions
- **Keyword Classification**: No LLM variability in intent classification
- **Hardcoded Responses**: Care advice and escalation scripts are fixed
- **No Randomness**: No temperature or sampling in core logic
- **100% Stability**: Perfect reproducibility across runs

## Evaluation Approach

### Policy Compliance
- Check for refunds without verification
- Validate escalation field completeness
- Monitor refund ceiling violations
- Detect privacy violations

### Helpfulness
- Keyword analysis of response quality
- Positive/negative indicator tracking
- Care advice provision detection
- Customer satisfaction proxies

### Stability
- Response similarity across runs
- Tool action consistency
- State transition reproducibility
- Deterministic behavior verification

## Technology Choices

- **LangGraph**: Workflow orchestration with state management
- **Deterministic Rules**: Policy enforcement through code
- **Keyword Matching**: Intent classification for stability
- **Tool Wrappers**: Safety layer for all operations
- **Session State**: Conversation context management
- **JSON Logging**: Audit trail for all actions

## Security Considerations

- **No Direct Tool Access**: LLM cannot execute tools directly
- **Policy Validation**: All actions checked before execution
- **Verification Gates**: Sensitive operations require verification
- **Escalation Latch**: Prevents policy bypass after escalation
- **Audit Trail**: All actions recorded for compliance review

## Failure Modes

- **Policy Violations**: Impossible by design (deterministic enforcement)
- **Verification Failures**: Graceful handling with escalation path
- **Tool Failures**: Error messages maintain policy compliance
- **Escalation Failures**: Fallback to standard escalation scripts
- **Classification Errors**: Conservative routing to verification when uncertain