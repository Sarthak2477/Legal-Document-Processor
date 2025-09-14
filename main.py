"""
Example usage of the contract processing pipeline.
"""
import logging
from pathlib import Path
from pipeline.orchestrator import ContractPipeline
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Example usage of the contract processing pipeline."""
    
    # TODO: Initialize pipeline
    pipeline = ContractPipeline(config={
        'use_layoutlm': False  # Set to True to use LayoutLMv3
    })
    
    # TODO: Example single contract processing
    contract_file = "sample_contract.pdf"  # Replace with actual file path
    
    if Path(contract_file).exists():
        result = pipeline.process_contract(
            file_path=contract_file,
            output_dir="./output"
        )
        
        if result['success']:
            print(f"✓ Contract processed successfully!")
            print(f"Summary: {result['analysis']['summary'][:200]}...")
        else:
            print(f"✗ Processing failed: {result['error']}")
    else:
        print("Sample contract file not found. Please add a PDF file to test.")
    
    # TODO: Example batch processing
    batch_dir = "./contracts"  # Directory containing multiple contracts
    if Path(batch_dir).exists():
        file_paths = list(Path(batch_dir).glob("*.pdf"))
        if file_paths:
            results = pipeline.process_batch(
                file_paths=[str(f) for f in file_paths],
                output_dir="./batch_output"
            )
            print(f"Processed {len(results)} contracts in batch.")
    
    # TODO: Example Q&A usage
    # Assuming we have a processed contract
    # answer = pipeline.rag_generator.answer_questions(
    #     "What are the payment terms?",
    #     processed_contract
    # )
    # print(f"Answer: {answer}")


if __name__ == "__main__":
    main()