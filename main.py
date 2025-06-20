import openai
import yaml
import os
from dotenv import load_dotenv
os.environ.pop("SSL_CERT_FILE", None)

load_dotenv('env.env')
OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME")


client = openai.OpenAI(api_key=OPEN_API_KEY)
def read_task_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
    
def extract_task_information(task_yaml):
    """Step 1: Let LLM read and extract all important information from task.yaml"""
    extraction_prompt = f"""
Analyze this YAML configuration and extract key information for Streamlit application development:

YAML Content:
{yaml.dump(task_yaml, default_flow_style=False)}

Extract and organize:

1. **CORE FUNCTIONALITY**:
   - Task type and main purpose
   - Input/output requirements and formats
   - Data processing workflow

2. **API INTEGRATION**:
   - API endpoint and authentication
   - Request payload structure (field names only, not descriptions)
   - Response format and data extraction method
   - Required data preprocessing/encoding

3. **UI REQUIREMENTS**:
   - Input methods (upload, text, dropdowns)
   - Display components (tables, charts, images)
   - Layout and interaction elements

4. **TECHNICAL SPECS**:
   - File format support
   - Performance constraints
   - Required libraries

Return as structured JSON-like format for code generation.
"""
    
    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[{"role": "user", "content": extraction_prompt}]
    )
    
    extracted_info = response.choices[0].message.content
    print("✅ Step 1: Task information extracted")
    return extracted_info

def build_code_generation_prompt(extracted_info, task_yaml):
    """Step 2: Create comprehensive prompt for code generation using extracted information"""
    # Get specific technical details
    api_url = task_yaml.get('model_information', {}).get('api_url', 'API_URL_NOT_SPECIFIED')
    sample_path = task_yaml.get('dataset_description', {}).get('data_path', './data')
    output_type = task_yaml.get('model_information', {}).get('output_format', {}).get('type', 'unknown')
    input_keys = list(task_yaml['model_information']['input_format']['structure'].keys())
    first_key = input_keys[0] if input_keys else 'data'
    print(sample_path)
    prompt = f"""
IMPORTANT INSTRUCTIONS FOR CODE GENERATION:
- The path will be the absolute path to the folder containing task.yaml, the data folder, and any additional files or folders. Use this path as the root for all file and folder access. Do not assume a subfolder unless it is specified in task.yaml.
- The dataset may have a specific folder hierarchy (e.g., subfolders for classes, speakers, or other groupings). DO NOT simply process all files in the root folder. Instead, process files and folders according to the structure and requirements described in task.yaml (for example, only use files in certain subfolders, or follow the class/subclass structure as described).
- Add an option (e.g., a button or checkbox) to allow the user to run task and see results for the samples in data_source/data_path if provided. If this option is selected, process and display results for the sample data.
- If the path does not exist, show an error message in the UI.

Generate a complete, production-ready Streamlit application based on these requirements:

REQUIREMENTS:
{extracted_info}

TECHNICAL SPECS:
- API Endpoint: {api_url}
- Sample Path: {sample_path}
- Output Format: {output_type}

CRITICAL API RULES:
1. Payload structure: Use only {input_keys} as keys, not descriptions
   - Example: {{{first_key}: "actual_value"}}
2. Response handling: API response has "data" field containing {output_type} with a list wrapper
   - Get response: response_json = response.json()
   - There are 2 circumstances:
        - Example: 
        def inspect_structure(data):
            if isinstance(data, list):
                if all(isinstance(item, dict) for item in data):
                    return data
                elif all(isinstance(item, list) and all(isinstance(sub, dict) for sub in item) for item in data):
                    return data[0]
        - First, there's no list wrapper, we just use data = response_json["data"]
        - Second, there's a list wrapper, we use data = response_json["data"][0] to unwrap the wrapper
        We have to try the first, then check if the type(data) = {output_type}, then we stop, else we check the 2nd circumstance
   - The data be in format: {output_type}

IMPLEMENTATION REQUIREMENTS:
- Complete Streamlit app with all imports
- Proper error handling and validation
- User-friendly interface with progress indicators
- The st.image() function should no longer use the deprecated use_column_width=True parameter. Instead, always use use_container_width=True for resizing images to fit the layout. Do not include deprecated or removed arguments
- Do not use the deprecated .render() method on Styler objects — it has been removed since pandas 1.3. Instead, always use .to_html() when exporting styled DataFrames to HTML. Ensure your code is compatible with modern pandas versions.
- Do not use the deprecated ImageDraw.textsize() method. Instead, use textbbox() if you need the bounding box (width and height) of the text, or textlength() if you only need the text length. Ensure all code is compatible with the latest Pillow versions.
- Carefuly check the hashable error.
- Caching with @st.cache_data where appropriate
- Bug-free, production-ready code only
- No explanations or markdown formatting

Generate the complete Python code now.
"""
    return prompt

def build_review_prompt(generated_code, task_yaml):
    """Step 3: Create prompt for final code review and bug fixing"""
    api_url = task_yaml.get('model_information', {}).get('api_url', 'API_URL_NOT_SPECIFIED')
    output_type = task_yaml.get('model_information', {}).get('output_format', {}).get('type', 'unknown')
    input_keys = list(task_yaml['model_information']['input_format']['structure'].keys())
    first_key = input_keys[0] if input_keys else 'data'
    review_prompt = f"""
Review this generated Streamlit code and fix ALL bugs/issues:

GENERATED CODE:
```python
{generated_code}
```

CONTEXT: 
- API Endpoint: {api_url}
- Output Format: {output_type}

CRITICAL CHECKS:
1. **API Integration**: 
   - Payload uses field names only (not descriptions)
   - Access pattern: 
        - If there's a wrapper : response_json = response.json() -> data = response_json["data"][0] -> results = data
        - If there's no wrapper: response_json = response.json() -> data = response_json["data"] -> results = data
        - Make sure the results is {output_type} format
   - Proper error handling for API calls

2. **Code Quality**:
   - All imports present and correct (io, sys, ..., all used lib must be include)
   - Verify the validity of all use function from external library, some maybe deprecated or remove
   - No syntax errors or undefined variables
   - Proper Streamlit components and caching
   - User-friendly error messages
   - Input validation

3. **Streamlit Best Practices**:
   - Fix any deprecated Streamlit parameters or methods
   - Ensure all Streamlit components use current API

4. **Functionality**:
   - Complete workflow implementation
   - File handling and data processing
   - UI components work correctly

OUTPUT:
- If perfect: Return exactly "CODE_APPROVED"
- If issues found: Return complete corrected code (no explanations)
"""
    return review_prompt

def main(task_yaml_path='task.yaml'):
    print("🚀 Starting Multi-Stage Code Generation Pipeline...")
    
    # Load task configuration
    task_yaml = read_task_yaml(task_yaml_path)
    output_type = task_yaml['model_information']['output_format']['type']
    print("📖 Task YAML loaded successfully")
    
    # Stage 1: Extract task information
    print("\n📋 Stage 1: Extracting task information...")
    extracted_info = extract_task_information(task_yaml)
    
    # Stage 2: Generate code using extracted information
    print("\n🔨 Stage 2: Generating Streamlit application code...")
    code_prompt = build_code_generation_prompt(extracted_info, task_yaml)
    generated_code = call_llm(code_prompt)
    
    if generated_code is None:
        print("❌ Failed to generate code")
        return None
    
    # Stage 3: Review and fix the generated code
    print("\n🔍 Stage 3: Reviewing and fixing generated code...")
    review_prompt = build_review_prompt(generated_code, task_yaml)
    reviewed_code = call_llm(review_prompt)
    
    if reviewed_code is None:
        print("❌ Failed to review code, using initial version")
        final_code = generated_code
    else:
        # Check if code needs fixing or is approved
        if reviewed_code.strip() == "CODE_APPROVED":
            print("✅ Generated code approved without changes")
            final_code = generated_code
        else:
            print("🔧 Code issues found and fixed")
            final_code = reviewed_code
    
    # Clean markdown markers if present
    final_code = clean_generated_code_str(final_code)
    print("\n🎉 Pipeline completed successfully!")
    return final_code

def call_llm(prompt):
    """Call OpenAI API with the given prompt"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        return None

def clean_generated_code_str(code_str):
    """Remove first and last lines from generated code string if they are markdown markers."""
    lines = code_str.splitlines(True)
    if len(lines) >= 2:
        if lines[0].strip().startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
    return ''.join(lines)

if __name__ == "__main__":
    # For standalone CLI use
    code = main()
    with open('generated_ui.py', 'w', encoding='utf-8') as f:
        f.write(code)