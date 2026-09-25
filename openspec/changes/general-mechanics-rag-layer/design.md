## Context
The TorqueAI system currently uses a RAG layer built from vehicle-specific service manuals. Users often ask general mechanical questions that are not specific to a vehicle (e.g., "How to use a torque wrench?", "What is the correct procedure for bleeding brakes?"). These questions are not well answered by the vehicle-specific manuals alone. We need to add a second RAG layer containing general mechanics knowledge to improve the assistant's ability to answer such questions.

Additionally, the `service_guide/general` folder contains duplicate PDF files that waste storage and processing time. We must deduplicate these files before ingestion.

Finally, we want to upgrade the LLM model to `qwen3.8:latest` for better reasoning capabilities.

## Goals / Non-Goals
### Goals
- Add a RAG layer for general mechanics documents.
- Deduplicate PDFs in `service_guide/general`.
- Change the default LLM model to `qwen3.8:latest`.
- Ensure the chat endpoint can query both RAG layers and combine results.

### Non-Goals
- Changing the embedding model (remains `bge-m3`).
- Altering the vehicle-specific RAG layer or its ingestion pipeline.
- Modifying the database schema or frontend.

## Decisions
### Decision 1: Architecture for the General Mechanics RAG Layer
- **Chosen Approach**: Create a second independent RAG layer with its own Qdrant collection (e.g., `general_mechanics`). The chat endpoint will query both the vehicle-specific collection (`automotive_manuals`) and the general mechanics collection, then merge the results.
- **Rationale**: Keeping the layers separate allows independent management, different ingestion schedules, and clear separation of concerns. It also avoids modifying the existing vehicle-specific RAG code, reducing risk.
- **Alternative Rejected**: Modifying the existing RAG layer to accept multiple sources would require significant changes to the ingestion and retrieval code, and could complicate the system.

### Decision 2: Deduplication Method
- **Chosen Approach**: Compute MD5 hashes of each PDF file in `service_guide/general` and remove duplicates, keeping the first encountered file.
- **Rationale**: MD5 is fast and sufficient for detecting identical files. This method is simple and can be implemented as a one-time script.
- **Alternative Rejected**: Using more complex similarity detection (e.g., comparing text content) is overkill for exact duplicates and would be slower.

### Decision 3: LLM Model Upgrade
- **Chosen Approach**: Change the default model in the chat endpoint from `qwen2.5:7b` to `qwen3.8:latest`.
- **Rationale**: The newer model is expected to have better reasoning and language understanding, which will improve the quality of generated answers.
- **Alternative Rejected**: Keeping the old model would miss the opportunity for improvement. Using an even larger model might be too slow or resource-intensive.

## Risks / Trade-offs
- **[Risk]** Increased resource usage (RAM, disk) due to a second RAG collection.
  - **Mitigation**: The general mechanics collection is expected to be smaller than the vehicle-specific one. We can monitor and adjust.
- **[Risk]** Potential for inconsistent or conflicting information between the two layers.
  - **Mitigation**: The general mechanics layer is intended for foundational knowledge, while the vehicle-specific layer contains model-specific procedures. We will design the prompt to prioritize vehicle-specific information when relevant.
- **[Risk]** The deduplication script might accidentally remove non-duplicate files if hash collisions occur (extremely unlikely with MD5).
  - **Mitigation**: We will log the duplicates removed and verify by checking the number of files before and after.

## Migration Plan
1. Run the deduplication script on `service_guide/general`.
2. Create the new Qdrant collection for general mechanics (if not already created by the ingestion script).
3. Ingest the deduplicated PDFs into the general mechanics collection.
4. Update the chat endpoint to query both collections and combine results.
5. Change the default LLM model to `qwen3.8:latest`.
6. Test the system with general and vehicle-specific questions.