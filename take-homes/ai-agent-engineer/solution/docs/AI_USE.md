# AI Tool Usage Disclosure

## Tools Used

- **Devin AI**: Primary AI assistant used throughout development for code generation, architecture planning, and debugging assistance.

## Usage Breakdown

### Code Generation & Architecture Planning
- Initial implementation plan and architecture design
- Generation of policy engine code structure and keyword matching logic
- Creation of intent classifier with keyword-based patterns
- Development of LangGraph workflow orchestration
- Implementation of tool wrapper layer for safety
- Generation of evaluation framework and metrics

### Manual Work
- Careful review and refinement of all AI-generated code
- Manual implementation of verification logic to ensure accuracy with Customer Care Guide
- Direct coding of escalation handling and latch mechanism
- Manual adjustment of care advice keyword matching from guide appendix
- Hands-on debugging of integration issues between components
- Manual testing and validation of policy compliance

### AI Rejections & Overrides
- **Rejected**: AI-suggested approach for direct LLM tool access
  - **Why**: This would have compromised policy boundaries by allowing the LLM to execute tools without policy validation
  - **Override**: Implemented tool wrapper pattern that forces all tool execution through deterministic policy checks

- **Rejected**: AI-proposed temperature-based sampling for response generation
  - **Why**: Would have introduced variability that could affect run-to-run stability
  - **Override**: Used deterministic response generation to ensure 100% reproducibility

- **Rejected**: AI-suggested complex entity extraction using LLM
  - **Why**: Would have introduced nondeterminism and potential policy interpretation by the model
  - **Override**: Implemented simple keyword-based extraction for stability

## Time Savings Estimate

AI tools accelerated development by approximately 40-50%, primarily through boilerplate generation and architectural planning. However, the core policy enforcement logic, verification requirements, and escalation handling required significant manual oversight to ensure strict compliance with the Customer Care Guide.

## Areas of Full Human Responsibility

- Understanding and interpreting the Customer Care Guide requirements
- Ensuring policy compliance enforcement is deterministic and not subject to LLM interpretation
- Designing the evaluation metrics to align with project requirements
- Manual testing and validation of the complete solution
- Final code review and quality assurance
