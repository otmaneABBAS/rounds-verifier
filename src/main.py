from .prompt_processor import process_data

def main() -> None:
    # File paths
    input_path = "data/sample.csv"  # Adjust path as needed
    output_path = "data/output.csv"
    
    # Process the data
    success = process_data(input_path, output_path)
    if success:
        print("Data processing completed successfully.")
    else:
        print("Data processing failed.")

if __name__ == "__main__":
    main()